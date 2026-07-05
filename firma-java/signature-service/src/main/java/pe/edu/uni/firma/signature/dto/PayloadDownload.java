package pe.edu.uni.firma.signature.dto;

/** DTO interno para descargar el documento visible extraído del contenedor firmado. */
public record PayloadDownload(
        String fileName,
        String contentType,
        byte[] bytes
) {}
