package pe.edu.uni.firma.signature.patterns.behavioral;

/** Patrón Command: encapsula una solicitud de firma documental. */
public record SignDocumentCommand(String dni, String fileName, String contentType, byte[] content) {}
