package pe.edu.uni.firma.signature.container;

public record SignedEnvelope(SignatureMetadata metadata, byte[] payloadBytes) {}
