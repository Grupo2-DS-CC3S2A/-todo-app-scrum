package pe.edu.uni.firma.signature.dto;

import java.time.Instant;

public record AuditResponse(
        Long id,
        String operation,
        String dni,
        Long documentId,
        String fileName,
        String algorithm,
        String hashHex,
        Boolean valid,
        Instant createdAt
) {}
