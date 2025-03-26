from transformers import StoppingCriteria, StoppingCriteriaList
import torch

class StopOnCodeBlockComplete(StoppingCriteria):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.start_marker = "```python"
        self.end_marker = "```"

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Decode tokens generated so far
        decoded_text = self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
        # Look for the opening code block marker
        start_index = decoded_text.find(self.start_marker)
        if start_index == -1:
            return False
        # Look for a closing marker after the start
        end_index = decoded_text.find(self.end_marker, start_index + len(self.start_marker))
        # If found, the code block is complete
        return end_index != -1
