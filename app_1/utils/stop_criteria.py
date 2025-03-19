
from transformers import StoppingCriteria, StoppingCriteriaList

class StopOnPatterns(StoppingCriteria):
    def __init__(self, patterns, tokenizer):
        """
        :param patterns: list of string patterns which signal that generation should stop.
        :param tokenizer: the tokenizer used to decode tokens.
        """
        self.patterns = patterns
        self.tokenizer = tokenizer

    def __call__(self, input_ids, scores, **kwargs):
        # Decode the generated tokens from the first example in the batch.
        generated_text = self.tokenizer.decode(input_ids[0], skip_special_tokens=True)
        # Stop if any of the patterns is found.
        return any(pattern in generated_text for pattern in self.patterns)