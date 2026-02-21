import tempfile
import warnings
from pathlib import Path
from itertools import combinations

import numpy as np
import cv2
import torch
import gradio as gr
from PIL import Image
from PIL.ExifTags import TAGS
from sklearn.metrics.pairwise import cosine_similarity
import kornia.feature as KF

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
DINO_THRESHOLD = 0.5
LOFTR_INLIER_THRESHOLD = 10
DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# 모델은 앱 시작 시 한 번만 로드
_dino_model = None
_loftr_model = None
_dust3r_model = None


def get_dino():
    global _dino_model
    if _dino_model is None:
        _dino_model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14", verbose=False)
        _dino_model.eval().to(DEVICE)
    return _dino_model


def get_loftr():
    global _loftr_model
    if _loftr_model is None:
        _loftr_model = KF.LoFTR(pretrained="outdoor")
        _loftr_model.eval().to(DEVICE)
    return _loftr_model


def get_dust3r():
    global _dust3r_model
    if _dust3r_model is None:
        from mini_dust3r.model import AsymmetricCroCo3DStereo
        _dust3r_model = AsymmetricCroCo3DStereo.from_pretrained(
            "naver/DUSt3R_ViTLarge_BaseDecoder_512_dpt"
        )
        _dust3r_model = _dust3r_model.to(DEVICE)
    return _dust3r_model


# ─────────────────────────────────────────────
# 동일 피사체 검증 (verify_same_subject.py 기반)
# ─────────────────────────────────────────────
def extract_embedding(model, image_path: Path) -> np.ndarray:
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    tensor = torch.tensor(np.array(img) / 255.0, dtype=torch.float32)
    tensor = tensor.permute(2, 0, 1).unsqueeze(0)
    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    std  = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    tensor = (tensor - mean) / std
    with torch.no_grad():
        emb = model(tensor.to(DEVICE))
    return emb.cpu().numpy()


def count_loftr_inliers(matcher, path_a: Path, path_b: Path) -> int:
    def load_gray(p, size=(640, 480)):
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, size)
        return torch.tensor(img / 255.0, dtype=torch.float32)[None, None].to(DEVICE)

    img_a = load_gray(path_a)
    img_b = load_gray(path_b)
    with torch.no_grad():
        out = matcher({"image0": img_a, "image1": img_b})
    kp_a = out["keypoints0"].cpu().numpy()
    kp_b = out["keypoints1"].cpu().numpy()
    if len(kp_a) < 4:
        return 0
    _, mask = cv2.findHomography(kp_a, kp_b, cv2.RANSAC, 5.0)
    return int(mask.sum()) if mask is not None else 0


def verify_same_subject(paths: list[Path]) -> tuple[bool, str]:
    dino = get_dino()
    loftr = get_loftr()

    embeddings = [extract_embedding(dino, p) for p in paths]

    pairs_to_check = []
    log_lines = []
    for i, j in combinations(range(len(paths)), 2):
        sim = cosine_similarity(embeddings[i], embeddings[j])[0][0]
        if sim >= DINO_THRESHOLD:
            pairs_to_check.append((i, j))
        log_lines.append(f"{paths[i].name} ↔ {paths[j].name}: DINOv2={sim:.3f}")

    parent = list(range(len(paths)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i, j in pairs_to_check:
        inliers = count_loftr_inliers(loftr, paths[i], paths[j])
        log_lines.append(f"  └ LoFTR inliers={inliers}")
        if inliers >= LOFTR_INLIER_THRESHOLD:
            union(i, j)

    roots = {find(i) for i in range(len(paths))}
    same = len(roots) == 1
    return same, "\n".join(log_lines)


# ─────────────────────────────────────────────
# DUSt3R 3D 재구성
# ─────────────────────────────────────────────
def align_mesh_upright(mesh, world_T_cam_b44: np.ndarray):
    """카메라 포즈에서 up 방향을 추정해 메시를 정렬하고 원점에 센터링"""
    # 각 카메라의 up 벡터 평균 (-Y 컬럼)
    up_vectors = -world_T_cam_b44[:, :3, 1]
    mean_up = up_vectors.mean(axis=0)
    norm = np.linalg.norm(mean_up)
    if norm < 1e-6:
        return mesh
    mean_up /= norm

    # mean_up → (0, 1, 0) 정렬
    target = np.array([0.0, 1.0, 0.0])
    axis = np.cross(mean_up, target)
    axis_norm = np.linalg.norm(axis)
    if axis_norm < 1e-6:
        return mesh
    axis /= axis_norm
    angle = np.arccos(np.clip(np.dot(mean_up, target), -1.0, 1.0))

    c, s = np.cos(angle), np.sin(angle)
    t = 1 - c
    x, y, z = axis
    R = np.array([
        [t*x*x + c,    t*x*y - s*z,  t*x*z + s*y],
        [t*x*y + s*z,  t*y*y + c,    t*y*z - s*x],
        [t*x*z - s*y,  t*y*z + s*x,  t*z*z + c  ],
    ])
    T = np.eye(4)
    T[:3, :3] = R
    mesh.apply_transform(T)

    # 원점 센터링
    mesh.apply_translation(-mesh.bounds.mean(axis=0))
    return mesh


def reconstruct_3d(paths: list[Path]) -> str:
    """3D 재구성 후 .glb 파일 경로 반환"""
    import copy
    from mini_dust3r.api.inference import scene_to_results
    from mini_dust3r.utils.image import load_images
    from mini_dust3r.inference import inference as dust3r_inference
    from mini_dust3r.image_pairs import make_pairs
    from mini_dust3r.cloud_opt import global_aligner, GlobalAlignerMode

    model = get_dust3r()

    imgs = load_images(folder_or_list=[str(p) for p in paths], size=512, verbose=True)
    if len(imgs) == 1:
        imgs = [imgs[0], copy.deepcopy(imgs[0])]
        imgs[1]["idx"] = 1

    pairs = make_pairs(imgs, scene_graph="complete", prefilter=None, symmetrize=True)
    output = dust3r_inference(pairs, model, DEVICE, batch_size=1)

    mode = GlobalAlignerMode.PointCloudOptimizer if len(imgs) > 2 else GlobalAlignerMode.PairViewer
    scene = global_aligner(dust3r_output=output, device=DEVICE, mode=mode)

    if mode == GlobalAlignerMode.PointCloudOptimizer:
        scene.compute_global_alignment(init="mst", niter=300, schedule="cosine", lr=0.01)

    # int로 명시해서 beartype 버그 우회, min_conf_thr 낮춰 포인트 더 살리기
    result = scene_to_results(scene, int(3))

    mesh = align_mesh_upright(result.mesh, result.world_T_cam_b44)

    tmp = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    mesh.export(tmp.name)
    return tmp.name


# ─────────────────────────────────────────────
# 모듈용 대표 함수 (API)
# ─────────────────────────────────────────────
def generate_3d_model(image_paths: list[str | Path], use_verify: bool = True) -> dict:
    """
    이미지들을 검증하고 DUSt3R로 3D 모델을 생성합니다.
    
    Args:
        image_paths: 이미지 파일 경로 리스트 (str 또는 Path)
        use_verify: 재구성 전 피사체 동일성 검증 여부
        
    Returns:
        dict: 처리 결과를 담은 딕셔너리
            - success (bool): 재구성 성공 여부
            - same_subject (bool | None): 동일 피사체 검증 통과 여부 (검증 안 했을 시 None)
            - mesh_path (str | None): 생성된 .glb 파일 경로
            - log (str): 전체 과정의 텍스트 로그
    """
    paths = [Path(p) for p in image_paths]
    if len(paths) < 2:
        raise ValueError("이미지를 2장 이상 제공해야 합니다.")

    log_lines = [f"디바이스: {DEVICE}", f"이미지 {len(paths)}장 수신"]
    same_subject = None
    glb_path = None

    # 1. 동일 피사체 검증
    if use_verify:
        log_lines.append("\n[ 동일 피사체 검증 중... ]")
        same_subject, verify_log = verify_same_subject(paths)
        log_lines.append(verify_log)
        
        if not same_subject:
            log_lines.append("\n✗ 동일한 피사체가 아닙니다. 3D 재구성을 건너뜁니다.")
            return {
                "success": False,
                "same_subject": False,
                "mesh_path": None,
                "log": "\n".join(log_lines)
            }
        log_lines.append("✓ 동일 피사체 확인")

    # 2. 3D 재구성
    log_lines.append("\n[ DUSt3R 3D 재구성 중... ]")
    try:
        glb_path = reconstruct_3d(paths)
        log_lines.append("✓ 3D 재구성 완료")
        success = True
    except Exception as e:
        log_lines.append(f"✗ 재구성 실패: {e}")
        success = False

    return {
        "success": success,
        "same_subject": same_subject,
        "mesh_path": glb_path,
        "log": "\n".join(log_lines)
    }


# ─────────────────────────────────────────────
# Gradio 앱 핸들러 & UI
# ─────────────────────────────────────────────
def gradio_process(files, use_verify):
    if not files or len(files) < 2:
        return "이미지를 2장 이상 업로드해주세요.", None
    
    paths = [Path(f) for f in files]
    result = generate_3d_model(paths, use_verify=use_verify)
    return result["log"], result["mesh_path"]


def create_ui():
    with gr.Blocks(title="3D 피사체 재구성") as demo:
        gr.Markdown("## 다각도 사진 → 3D 재구성\n동일 피사체 여부를 검증한 후 DUSt3R로 3D 모델을 생성합니다.")

        with gr.Row():
            with gr.Column():
                file_input = gr.File(
                    label="이미지 업로드 (2장 이상)",
                    file_count="multiple",
                    file_types=["image"],
                    type="filepath",
                )
                use_verify = gr.Checkbox(
                    label="동일 피사체 검증 후 재구성",
                    value=True,
                )
                run_btn = gr.Button("실행", variant="primary")

            with gr.Column():
                status_box = gr.Textbox(label="진행 상황", lines=15, interactive=False)
                model_viewer = gr.Model3D(label="3D 재구성 결과", clear_color=[0.1, 0.1, 0.1, 1.0])

        run_btn.click(
            fn=gradio_process,
            inputs=[file_input, use_verify],
            outputs=[status_box, model_viewer],
        )
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(share=False)