package pe.edu.uni.firma.signature.controller;

import io.swagger.v3.oas.annotations.Operation;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import pe.edu.uni.firma.signature.container.SignedDocumentEnvelopeService;
import pe.edu.uni.firma.signature.domain.SignedDocumentRecord;
import pe.edu.uni.firma.signature.dto.DocumentMetadataResponse;
import pe.edu.uni.firma.signature.dto.PayloadDownload;
import pe.edu.uni.firma.signature.dto.SignedDocumentResponse;
import pe.edu.uni.firma.signature.dto.VerifyDocumentResponse;
import pe.edu.uni.firma.signature.patterns.behavioral.SignDocumentCommand;
import pe.edu.uni.firma.signature.service.DocumentSignatureEmailService;
import pe.edu.uni.firma.signature.service.DocumentSignatureFacade;

@RestController
@RequestMapping("/api/documentos")
public class DocumentController {
    private final DocumentSignatureFacade facade;
    private final DocumentSignatureEmailService emailService;

    public DocumentController(DocumentSignatureFacade facade, DocumentSignatureEmailService emailService) {
        this.facade = facade;
        this.emailService = emailService;
    }

    @Operation(summary = "Firma cualquier archivo y genera un único contenedor .uni-signed con documento, hash, firma y certificado")
    @PostMapping(value = "/sign", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public SignedDocumentResponse sign(
            @RequestParam("dni") String dni,
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "email", required = false) String email,
            @RequestParam(value = "dependencia", required = false) String dependencia,
            @RequestParam(value = "documentType", required = false) String documentType
    ) throws IOException {
        if (file.isEmpty()) throw new IllegalArgumentException("El archivo está vacío");

        SignedDocumentResponse response = facade.sign(new SignDocumentCommand(
                dni,
                file.getOriginalFilename(),
                file.getContentType(),
                file.getBytes()
        ));

        if (email != null && !email.isBlank()) {
            SignedDocumentRecord storedDocument = facade.findDocument(response.id());
            PayloadDownload visiblePayload = facade.visiblePayloadFromStoredDocument(response.id());
            emailService.sendDocumentSubmittedEmail(
                    email,
                    dependencia,
                    response,
                    storedDocument,
                    visiblePayload
            );
        }

        return response;
    }

    @Operation(summary = "Lista documentos firmados de un DNI guardados en Base 3")
    @GetMapping("/dni/{dni}")
    public List<DocumentMetadataResponse> list(@PathVariable("dni") String dni) {
        return facade.listByDni(dni);
    }

    @Operation(summary = "Visualiza el documento encapsulado ya preparado para firma. Si es PDF, incluye sello visible")
    @GetMapping("/{id}/view")
    public ResponseEntity<byte[]> view(@PathVariable("id") Long id) {
        SignedDocumentRecord doc = facade.findDocument(id);
        String contentType = doc.contentType() == null ? MediaType.APPLICATION_OCTET_STREAM_VALUE : doc.contentType();
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.inline().filename(doc.originalFileName(), StandardCharsets.UTF_8).build().toString())
                .body(doc.documentBytes());
    }

    @Operation(summary = "Descarga el documento encapsulado original preparado para firma")
    @GetMapping("/{id}/download")
    public ResponseEntity<byte[]> download(@PathVariable("id") Long id) {
        SignedDocumentRecord doc = facade.findDocument(id);
        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment().filename(doc.originalFileName(), StandardCharsets.UTF_8).build().toString())
                .body(doc.documentBytes());
    }

    @Operation(summary = "Descarga el documento visible extraído. Si el original fue PDF, devuelve el PDF sellado")
    @GetMapping("/{id}/download-visible")
    public ResponseEntity<byte[]> downloadVisible(@PathVariable("id") Long id) {
        PayloadDownload payload = facade.visiblePayloadFromStoredDocument(id);
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(payload.contentType()))
                .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment().filename(payload.fileName(), StandardCharsets.UTF_8).build().toString())
                .body(payload.bytes());
    }

    @Operation(summary = "Descarga el archivo firmado único .uni-signed")
    @GetMapping("/{id}/download-signed")
    public ResponseEntity<byte[]> downloadSigned(@PathVariable("id") Long id) {
        SignedDocumentRecord doc = facade.findDocument(id);
        String fileName = doc.signedFileName() == null ? doc.originalFileName() + ".uni-signed" : doc.signedFileName();
        byte[] body = doc.signedFileBytes() == null ? doc.documentBytes() : doc.signedFileBytes();
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(SignedDocumentEnvelopeService.SIGNED_MEDIA_TYPE))
                .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment().filename(fileName, StandardCharsets.UTF_8).build().toString())
                .body(body);
    }

    @Operation(summary = "Obtiene el certificado lógico embebido en el archivo firmado")
    @GetMapping(value = "/{id}/certificate", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> certificate(@PathVariable("id") Long id) {
        SignedDocumentRecord doc = facade.findDocument(id);
        return ResponseEntity.ok(doc.certificateJson());
    }

    @Operation(summary = "Verifica un documento firmado guardado en Base 3")
    @PostMapping("/{id}/verify")
    public VerifyDocumentResponse verify(@PathVariable("id") Long id) {
        return facade.verify(id);
    }

    @Operation(summary = "Verifica manualmente un archivo .uni-signed subido por el usuario")
    @PostMapping(value = "/verify-upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public VerifyDocumentResponse verifyUpload(@RequestParam("file") MultipartFile file) throws IOException {
        if (file.isEmpty()) throw new IllegalArgumentException("Debe subir un archivo firmado .uni-signed");
        return facade.verifyUploaded(file.getBytes(), file.getOriginalFilename());
    }

    @Operation(summary = "Extrae y descarga el documento visible desde un contenedor .uni-signed subido manualmente")
    @PostMapping(value = "/extract-visible", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<byte[]> extractVisibleFromUpload(@RequestParam("file") MultipartFile file) throws IOException {
        if (file.isEmpty()) throw new IllegalArgumentException("Debe subir un archivo firmado .uni-signed");
        PayloadDownload payload = facade.visiblePayloadFromUploadedPackage(file.getBytes());
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(payload.contentType()))
                .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment().filename(payload.fileName(), StandardCharsets.UTF_8).build().toString())
                .body(payload.bytes());
    }

    @Operation(summary = "Elimina un documento firmado almacenado en Base 3 y sus registros de auditoría asociados")
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteDocument(@PathVariable("id") Long id) {
        facade.deleteDocument(id);
        return ResponseEntity.noContent().build();
    }
}
