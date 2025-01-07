
import tiktoken

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count tokens in a given text using the specified OpenAI model tokenizer.

    Args:
        text (str): The text to count tokens for.
        model (str): The model name to use for tokenization. Default is "gpt-3.5-turbo".

    Returns:
        int: The number of tokens in the text.
    """
    # Initialize the tokenizer for the specified model
    encoding = tiktoken.encoding_for_model(model)
    
    # Encode the text to get the token count
    token_count = len(encoding.encode(text))
    
    return token_count