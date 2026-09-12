# Grounded Generation And Citations

If retrieval returns no qualifying evidence, GroundStack returns its stable
insufficient-evidence response without calling the model.

For supported questions, the API sends only the bounded evidence set and recent authorized
conversation context to the configured OpenAI-compatible provider. The system prompt labels
document text as untrusted evidence and instructs the model not to follow instructions found
inside it.

The answer may cite only the source IDs included in the request. GroundStack validates every
citation against the retrieved evidence. A fabricated or missing required citation triggers one
bounded repair attempt; an invalid result is not saved as a grounded completed answer.

The browser receives streaming status and answer events. Raw provider errors are normalized
into a concise recoverable message.

The `fake` provider exists only for deterministic automated tests. It must not be used as
evidence that a real language-model request worked.
