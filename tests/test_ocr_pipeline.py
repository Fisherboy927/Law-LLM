from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from law_llm import ocr_pipeline
from law_llm.ocr_pipeline import OCRRecord


def test_group_name_from_filename_handles_page_suffixes() -> None:
    assert ocr_pipeline._group_name_from_filename("Answer_20_page1.png") == "Answer_20"
    assert ocr_pipeline._group_name_from_filename("Answer_20_Page10.png") == "Answer_20"
    assert ocr_pipeline._group_name_from_filename("Answer_20-p2.jpg") == "Answer_20"


def test_iter_image_paths_uses_natural_order(tmp_path) -> None:
    for name in ["Answer_01_page10.png", "Answer_01_page2.png", "Answer_01_page1.png"]:
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    assert [path.name for path in ocr_pipeline.iter_image_paths(tmp_path)] == [
        "Answer_01_page1.png",
        "Answer_01_page2.png",
        "Answer_01_page10.png",
    ]


def test_extract_text_from_paddle_json_payload() -> None:
    output = [
        SimpleNamespace(
            json={
                "parsing_res_list": [
                    {"block_content": "First block"},
                    {"block_content": "Second block"},
                ]
            }
        )
    ]

    assert ocr_pipeline._extract_text_from_paddle_result(output) == "First block\nSecond block"


def test_extract_text_from_paddle_markdown_payload() -> None:
    output = [SimpleNamespace(markdown={"markdown_texts": ["# Heading", "Body"]})]

    assert ocr_pipeline._extract_text_from_paddle_result(output) == "# Heading\nBody"


def test_paddleocr_pipeline_kwargs_reads_supported_environment(monkeypatch) -> None:
    monkeypatch.setenv("PADDLEOCR_PIPELINE_VERSION", "v1.6")
    monkeypatch.setenv("PADDLEOCR_DEVICE", "cpu")
    monkeypatch.setenv("PADDLEOCR_ENGINE", "transformers")
    monkeypatch.setenv("PADDLEOCR_VL_REC_MODEL_DIR", "/models/vl")
    monkeypatch.setenv("PADDLEOCR_USE_DOC_UNWARPING", "true")
    monkeypatch.setenv("PADDLEOCR_FORMAT_BLOCK_CONTENT", "false")
    monkeypatch.setenv("PADDLEOCR_VL_REC_MAX_CONCURRENCY", "4")

    assert ocr_pipeline._paddleocr_pipeline_kwargs() == {
        "pipeline_version": "v1.6",
        "device": "cpu",
        "engine": "transformers",
        "vl_rec_model_dir": "/models/vl",
        "use_doc_unwarping": True,
        "format_block_content": False,
        "vl_rec_max_concurrency": 4,
    }


def test_default_paddle_device_uses_gpu_when_cuda_is_available(monkeypatch) -> None:
    monkeypatch.delenv("PADDLEOCR_DEVICE", raising=False)
    monkeypatch.setattr(ocr_pipeline, "_paddle_cuda_status", lambda: (True, 1))

    assert ocr_pipeline.default_paddle_device() == "gpu:0"


def test_default_paddle_device_uses_env_override(monkeypatch) -> None:
    monkeypatch.setenv("PADDLEOCR_DEVICE", "cuda:0")

    assert ocr_pipeline.default_paddle_device() == "gpu:0"


def test_require_paddle_gpu_rejects_cpu_only_install(monkeypatch) -> None:
    monkeypatch.setattr(ocr_pipeline, "_paddle_cuda_status", lambda: (False, 0))

    with pytest.raises(RuntimeError, match="not installed with CUDA support"):
        ocr_pipeline.require_paddle_gpu("gpu:0")


def test_create_paddleocr_pipeline_passes_device_and_uses_cache(monkeypatch) -> None:
    calls = []

    class FakePaddleOCRVL:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    fake_paddleocr = SimpleNamespace(PaddleOCRVL=FakePaddleOCRVL)
    fake_paddle = SimpleNamespace(
        is_compiled_with_cuda=lambda: True,
        device=SimpleNamespace(
            cuda=SimpleNamespace(device_count=lambda: 1),
            set_device=lambda device: calls.append({"set_device": device}),
        ),
    )
    monkeypatch.setitem(sys.modules, "paddleocr", fake_paddleocr)
    monkeypatch.setitem(sys.modules, "paddle", fake_paddle)
    monkeypatch.setattr(ocr_pipeline, "_PADDLEOCR_PIPELINES", {})

    first = ocr_pipeline._get_paddleocr_pipeline("gpu:0", require_gpu=True)
    second = ocr_pipeline._get_paddleocr_pipeline("gpu:0", require_gpu=True)
    cpu = ocr_pipeline._get_paddleocr_pipeline("cpu")

    assert first is second
    assert cpu is not first
    assert {"set_device": "gpu:0"} in calls
    assert {"set_device": "cpu"} in calls
    assert {"pipeline_version": "v1.6", "device": "gpu:0"} in calls
    assert {"pipeline_version": "v1.6", "device": "cpu"} in calls


def test_save_paddle_result_uses_official_result_methods(tmp_path) -> None:
    calls = []

    class Result:
        def save_to_json(self, save_path):
            calls.append(("json", save_path))

        def save_to_markdown(self, save_path):
            calls.append(("markdown", save_path))

    ocr_pipeline._save_paddle_result([Result()], tmp_path / "raw")

    assert calls == [
        ("json", tmp_path / "raw"),
        ("markdown", tmp_path / "raw"),
    ]


def test_extract_and_stitch_data_groups_pages_in_order(tmp_path, monkeypatch) -> None:
    for name in ["Answer_01_page2.png", "Answer_01_page1.png", "Answer_02_page1.png"]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    text_by_name = {
        "Answer_01_page1.png": "first",
        "Answer_01_page2.png": "second",
        "Answer_02_page1.png": "other",
    }

    monkeypatch.setattr(
        ocr_pipeline,
        "ocr_image",
        lambda path, **kwargs: text_by_name[path.name],
    )

    assert ocr_pipeline.extract_and_stitch_data(tmp_path) == [
        OCRRecord(id="original_Answer_01", content="first second"),
        OCRRecord(id="original_Answer_02", content="other"),
    ]


def test_extract_and_stitch_data_can_preserve_markdown_page_breaks(tmp_path, monkeypatch) -> None:
    for name in ["Answer_01_page1.png", "Answer_01_page2.png"]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    text_by_name = {
        "Answer_01_page1.png": "# Heading\n\n first   page ",
        "Answer_01_page2.png": "second\npage",
    }

    monkeypatch.setattr(
        ocr_pipeline,
        "ocr_image",
        lambda path, **kwargs: text_by_name[path.name],
    )

    assert ocr_pipeline.extract_and_stitch_data(tmp_path, preserve_markdown=True) == [
        OCRRecord(
            id="original_Answer_01",
            content="# Heading\n\nfirst page\n\n---\n\nsecond\npage",
        )
    ]


def test_extract_and_stitch_data_can_skip_bad_images(tmp_path, monkeypatch) -> None:
    (tmp_path / "Answer_01_page1.png").write_text("x", encoding="utf-8")
    (tmp_path / "Answer_02_page1.png").write_text("x", encoding="utf-8")

    def fake_ocr(path, **kwargs):
        if path.name == "Answer_01_page1.png":
            raise RuntimeError("bad image")
        return "usable text"

    monkeypatch.setattr(ocr_pipeline, "ocr_image", fake_ocr)

    with pytest.warns(UserWarning, match="Skipping unreadable image"):
        records = ocr_pipeline.extract_and_stitch_data(tmp_path)

    assert records == [OCRRecord(id="original_Answer_02", content="usable text")]


def test_create_paddleocr_pipeline_has_actionable_import_error(monkeypatch) -> None:
    def fake_import(name, *args, **kwargs):
        if name == "paddleocr":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(ImportError, match="PaddleOCR-VL is required"):
        ocr_pipeline._create_paddleocr_pipeline()
