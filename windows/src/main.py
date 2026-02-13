import os
import sys
import time
import torch
import threading
import itertools
from diffusers import LTXVideoPipeline
from diffusers.utils import load_video, export_to_video

class HiggsfieldTool:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = "ltx-2-19b-distilled.safetensors"
        self.pipeline = None
        self.stop_spinner = False

    def spinner(self, message):
        chars = itertools.cycle(['|', '/', '-', '\\'])
        while not self.stop_spinner:
            sys.stdout.write(f'\r{message} {next(chars)} ')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * (len(message) + 10) + '\r')

    def load_model(self):
        if self.pipeline is None:
            self.pipeline = LTXVideoPipeline.from_single_file(
                self.model_path, 
                torch_dtype=torch.bfloat16
            ).to(self.device)

    def process_video(self, video_path, prompt, fps, strength=0.75):
        try:
            video_input = load_video(video_path)
            output = self.pipeline(
                prompt=prompt,
                video=video_input,
                strength=strength,
                num_frames=len(video_input),
                num_inference_steps=25
            ).frames[0]
            
            out_name = f"filtered_{os.path.basename(video_path)}"
            export_to_video(output, out_name, fps=fps)
            return True, out_name
        except Exception as e:
            return False, str(e)

    def run(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("========================================")
            print("      HIGGSFIELD AI VIDEO FILTER        ")
            print("========================================")
            
            paths_input = input("\n[>] Drag videos here (or 'q' to quit): ").strip()
            if paths_input.lower() == 'q': break
            
            # Clean paths from drag-and-drop quotes
            paths = [p.strip('"') for p in paths_input.split('" "') if p.strip()]
            if not paths: paths = [paths_input.strip('"')]

            prompt = input("[>] Enter filter prompt: ")
            try:
                fps = int(input("[>] Enter output FPS [24]: ") or 24)
            except:
                fps = 24

            self.stop_spinner = False
            spin_thread = threading.Thread(target=self.spinner, args=("Loading Model...",))
            spin_thread.start()
            self.load_model()
            self.stop_spinner = True
            spin_thread.join()

            for vid in paths:
                if not os.path.exists(vid): continue
                
                self.stop_spinner = False
                process_spin = threading.Thread(target=self.spinner, args=(f"Filtering {os.path.basename(vid)}...",))
                process_spin.start()
                
                success, result = self.process_video(vid, prompt, fps)
                self.stop_spinner = True
                process_spin.join()

                if success:
                    print(f"[✓] SUCCESS: {result}")
                else:
                    print(f"[X] FAIL: {os.path.basename(vid)} - {result}")

            input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    tool = HiggsfieldTool()
    tool.run()