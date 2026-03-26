import torch 
import numpy as np 
from PIL import Image 
import groundingdino.datasets.transforms as T
from groundingdino.util.inference import load_model, predict
import re
import requests
import json
import os

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")

class PerceptionModule:
    def __init__(self, config_path, weight_path , device="cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initializes VLM Which for now is just Grounding Dino 
        """
        print(f"Grounding dino loaded with {device}")
        self.device = device
        self.model = load_model(config_path,weight_path).to(self.device)
        self.transform = T.Compose([
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _parse_prompt_ollama(self,prompt: str) -> tuple:
        """
        Uses local Ollama qwen 2.5 to parse natural language 
        prompt into target and destination object names
        
        Args:
            prompt (str): The natural language command
        Returns:
            ("red cube", "blue bowl")
        """

        system_prompt = (
            "You are a robot assistant. "
            "From the instruction, identify: "
            "1) 'target': the object to be picked up "
            "2) 'destination': the container or location to place it in. "
            "The destination is always a bowl, container, or surface. "
            "Return only a JSON object with exactly two keys: target and destination. "
            "Values should be simple color+shape descriptions like 'red cube' or 'blue bowl'. "
                    f"Instruction: {prompt}"
        )
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "qwen2.5:0.5b",
                    "prompt": system_prompt,
                    "stream": False
                },
                timeout=30,
            )
            raw = resp.json().get("response", "")

            raw= re.sub(r'```[a-z]*',"",raw).strip("`").strip()
            parsed = json.loads(raw)
            assert "target" in parsed and "destination" in parsed
            return parsed["target"], parsed["destination"]
        
        except Exception as e:
            print(f"[Ollama] Failed: {e}, falling back to regex")
            return self._parse_prompt_regex(prompt)
        

    def _parse_prompt_regex(self, command: str) -> tuple :
        """
        Parses the command to extract the target and destination objects.
        works for both active and passive voice sentences and 
        In case the local Ollama API fails it falls back to reg ex
        """

        command = command.lower()

        # Pattern 1: Action -> Target -> Preposition -> Destination
        # e.g., "pick up the red cube and drop it into the blue bowl"
        match1 = re.search(r'(?:pick up|grab|take)?\s*(?:the\s+)?(.*?)\s+(?:and\s+)?(?:drop it|place it|put it)?\s*(?:into|in|on)\s+(?:the\s+)?(.*)', command)
        
        # Pattern 2: Preposition -> Destination -> Action -> Target
        # e.g., "in the blue bowl keep the red cube"
        match2 = re.search(r'(?:in|into|on)\s+(?:the\s+)?(.*?)\s+(?:keep|put|place|drop)\s+(?:the\s+)?(.*)', command)

        if match2:
            return match2.group(2).strip(), match2.group(1).strip()
        elif match1:
            return match1.group(1).strip(), match1.group(2).strip()
        else:
            raise ValueError(f"Could not parse the command format: '{command}'")

    def _preprocess_image(self, rgb_image: np.ndarray):
        """
        Converts Raw numpy(opencv) format images to Pytorch tensor format required
        by the Transformer 
        """
        img_pil = Image.fromarray(rgb_image)
        image_transformed, _ = self.transform(img_pil, None)
        return image_transformed
    
    def get_grasp_and_place_centroids(self,rgb_image: np.ndarray, command: str, box_threshold=0.3, text_threshold=0.25):
        """
        Performs zero shot detection to find (u,v) pixel coordinates
        
        Logic: 
        1. Parse the commande and get target and destination
        2. Query Grounding Dino with a prompt like "target_obj . dest_obj"
        3. Iterate through detections and map them to roles based on the phrase
        4. Return the (u,v) coordinates of the target and destination
        """
        target_obj, dest_obj = self._parse_prompt_ollama(command)

        dino_prompt = f"{target_obj} . {dest_obj}"

        image_tensor = self._preprocess_image(rgb_image)

        boxes , logits , phrases = predict(
            model=self.model,
            caption=dino_prompt,
            image=image_tensor,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
        )

        img_h , img_w ,_ = rgb_image.shape

        results: dict = {"target": None, "destination": None}
        best_scores = {"target": -1.0, "destination": -1.0}

        print(f"  [Perception] Parsed: target='{target_obj}', dest='{dest_obj}'")
        print(f"  [Perception] DINO detections: {len(boxes)} boxes")

        for box, logit, phrase in zip(boxes, logits, phrases):
            cx_norm, cy_norm, _, _ = box.numpy()
            score = float(logit)

            u = int(cx_norm * img_w)
            v = int(cy_norm * img_h)

            print(f"    Box ({u},{v}) score={score:.3f} phrase='{phrase}'")

            # Check target match (bidirectional substring)
            is_target = target_obj in phrase or phrase in target_obj
            # Check destination match
            is_dest = dest_obj in phrase or phrase in dest_obj

            if is_target and not is_dest and score > best_scores["target"]:
                results["target"] = (u, v)
                best_scores["target"] = score
            elif is_dest and not is_target and score > best_scores["destination"]:
                results["destination"] = (u, v)
                best_scores["destination"] = score
            elif is_target and is_dest:
                # Ambiguous — assign to whichever role still needs filling or has lower score
                if best_scores["target"] < best_scores["destination"]:
                    if score > best_scores["target"]:
                        results["target"] = (u, v)
                        best_scores["target"] = score
                else:
                    if score > best_scores["destination"]:
                        results["destination"] = (u, v)
                        best_scores["destination"] = score

        return results

if __name__ == "__main__":
    CONFIG = "models/grounding_dino/GroundingDINO_SwinT_OGC.py" 
    WEIGHTS = "models/grounding_dino/groundingdino_swint_ogc.pth"
    
    perception = PerceptionModule(CONFIG, WEIGHTS)
    
    # Mock image (H, W, 3) 
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8) 

    print()
    print()
    
    # Test Normal Prompt
    prompt_1 = "Pick up the red cube and drop it into the blue bowl"
    print(f"Testing normal prompt: {perception._parse_prompt_ollama(prompt_1)}")
    
    # Test Inverted Prompt
    prompt_2 = "in the blue bowl keep the red cube"
    print(f"Testing inverted prompt: {perception._parse_prompt_ollama(prompt_2)}")