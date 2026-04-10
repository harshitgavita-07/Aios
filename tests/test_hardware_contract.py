import hardware


def test_recommended_llamacpp_backend_prefers_best_available_backend():
    hw = {"llamacpp_backends": ["vulkan", "cpu"]}

    assert hardware._get_recommended_llamacpp_backend(hw) == "vulkan"


def test_recommend_gguf_model_uses_largest_tier_that_fits_budget():
    hw = {"ram_gb": 24.0, "vram_gb": 0.0}
    models = [
        "gemma-3-1b-it",
        "llama-3.2-3b-instruct",
        "llama-3.1-8b-instruct",
    ]

    assert hardware.recommend_gguf_model(hw, models, "cpu") == "llama-3.2-3b-instruct"
