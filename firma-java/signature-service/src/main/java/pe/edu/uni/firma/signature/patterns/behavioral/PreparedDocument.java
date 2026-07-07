package pe.edu.uni.firma.signature.patterns.behavioral;

public record PreparedDocument(
        String fileName,
        String contentType,
        byte[] content,
        boolean pdfStamped
) {}
