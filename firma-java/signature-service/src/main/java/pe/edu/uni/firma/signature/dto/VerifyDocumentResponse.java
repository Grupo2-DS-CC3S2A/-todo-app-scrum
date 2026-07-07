package pe.edu.uni.firma.signature.dto;

public record VerifyDocumentResponse(
        Long documentId,
        String dni,
        String apellidosNombres,
        String ubigeo,
        String originalFileName,
        String signedFileName,
        boolean valid,
        boolean hashValid,
        boolean signatureValid,
        boolean certificateTrusted,
        String message,
        String algorithm,
        String hashHex,
        String certificateIssuer,
        String signedAt,
        String verificationMode
) {}
