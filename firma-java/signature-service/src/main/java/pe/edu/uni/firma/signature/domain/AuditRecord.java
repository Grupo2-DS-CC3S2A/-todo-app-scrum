package pe.edu.uni.firma.signature.domain;

import java.time.Instant;

public record AuditRecord(
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
