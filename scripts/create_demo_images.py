from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def _draw_text_image(text: str, out_path: Path) -> None:
    image = Image.new("RGB", (1400, 350), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((30, 30), text, fill=(0, 0, 0))
    image.save(out_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create local OCR demo images.")
    parser.add_argument(
        "--output-dir",
        default="demo_inputs/images",
        help="Directory where demo images are written.",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _draw_text_image(
        "Candidate led a university legal clinic team, coordinated deadlines, and improved client communication outcomes.",
        output_dir / "answer_01_page1.png",
    )
    _draw_text_image(
        "Candidate resolved a client complaint by clarifying expectations and delivering a precise action plan.",
        output_dir / "answer_01_page2.png",
    )
    _draw_text_image(
        "Candidate used commercial awareness from internships to evaluate legal risk and present concise advice.",
        output_dir / "answer_02_page1.png",
    )

    print(f"Created demo images in {output_dir.resolve()}")
