"""Safe provider diagnostics: never expose raw errors, keys, or patient data."""


class ScreeningUnavailableError(RuntimeError):
    pass


def provider_error(exc: Exception) -> ScreeningUnavailableError:
    code = getattr(exc, "code", None)
    if code == 404:
        message = "The configured Gemini model is unavailable. Update GEMINI_MODEL in .env and restart the backend."
    elif code == 429:
        message = "Gemini's request limit or quota has been reached. Check your API project's quota and billing, or try again later."
    elif code in {401, 403}:
        message = "Gemini rejected access. Check your API key, its permissions, and API availability for your project."
    elif code == 400:
        message = "Gemini rejected the request. Check the API key and model configuration."
    elif code in {500, 502, 503, 504}:
        message = "Gemini is temporarily unavailable. Please try again shortly."
    else:
        message = "Could not connect to Gemini. Check your internet connection and try again."
    return ScreeningUnavailableError(message + " No assessment was produced.")
