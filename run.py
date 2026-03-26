"""
VLA Pick-and-Place Pipeline — Entry Point

Usage:
    python run.py --prompt "Pick up the red cube and place it in the blue bowl"
"""

from src.pipeline import VLAPipeline, CONFIG, WEIGHTS, CAM_POS, CAM_TARGET, CAM_UP
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description="VLA Pick and Place Pipeline")
    parser.add_argument("--prompt", type=str, required=True, help="Natural language command")
    args = parser.parse_args()

    pipeline = VLAPipeline(CONFIG, WEIGHTS, CAM_POS, CAM_TARGET, CAM_UP)

    try:
        pipeline.setup_system()
        success = pipeline.execute_task(args.prompt)

        if success:
            print("\n[Pipeline] Task completed successfully")
            time.sleep(3)
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
    finally:
        pipeline.teardown()


if __name__ == "__main__":
    main()
