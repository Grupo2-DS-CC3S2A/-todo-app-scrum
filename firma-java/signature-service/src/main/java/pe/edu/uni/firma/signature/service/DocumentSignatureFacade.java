package pe.edu.uni.firma.signature.service;

import java.time.Instant;
import java.util.List;
import org.springframework.stereotype.Service;
import pe.edu.uni.firma.common.crypto.KeyMaterialCodec;
import pe.edu.uni.firma.common.crypto.OriginalCryptoAdapter;
import pe.edu.uni.firma.signature.client.IdentityKeyClient;
import pe.edu.uni.firma.signature.container.EmbeddedCertificate;
import pe.edu.uni.firma.signature.container.SignatureMetadata;
import pe.edu.uni.firma.signature.container.SignedDocumentEnvelopeService;
import pe.edu.uni.firma.signature.container.SignedEnvelope;
import pe.edu.uni.firma.signature.domain.AuditRecord;
import pe.edu.uni.firma.signature.domain.SignedDocumentRecord;
import pe.edu.uni.firma.signature.dto.AuditResponse;
import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;
import pe.edu.uni.firma.signature.dto.CitizenPublicDto;
import pe.edu.uni.firma.signature.dto.DocumentMetadataResponse;
import pe.edu.uni.firma.signature.dto.PayloadDownload;
import pe.edu.uni.firma.signature.dto.SignedDocumentResponse;
import pe.edu.uni.firma.signature.dto.VerifyDocumentResponse;
import pe.edu.uni.firma.signature.patterns.behavioral.DocumentPreprocessorRegistry;
import pe.edu.uni.firma.signature.patterns.behavioral.PreparedDocument;
import pe.edu.uni.firma.signature.patterns.behavioral.RsaModularVerificationStrategy;
import pe.edu.uni.firma.signature.patterns.behavioral.SignDocumentCommand;
import pe.edu.uni.firma.signature.patterns.creational.SignedEnvelopeFactory;
import pe.edu.uni.firma.signature.repository.AuditRepository;
import pe.edu.uni.firma.signature.repository.SignedDocumentRepository;

/** Patrón Facade: caso de uso completo para firma, encapsulado, almacenamiento, descarga y verificación. */
@Service
public class DocumentSignatureFacade {
    public static final String ALGORITHM = "SHA-256 + RSA modular original + contenedor UNI";

    private final IdentityKeyClient identityClient;
    private final SignedDocumentRepository documentRepository;
    private final AuditRepository auditRepository;
    private final RsaModularVerificationStrategy verificationStrategy;
    private final DocumentPreprocessorRegistry preprocessorRegistry;
    private final SignedEnvelopeFactory envelopeFactory;
    private final SignedDocumentEnvelopeService envelopeService;
    private final KeyMaterialCodec codec = new KeyMaterialCodec();
    private final OriginalCryptoAdapter crypto = new OriginalCryptoAdapter();

    public DocumentSignatureFacade(IdentityKeyClient identityClient,
                                   SignedDocumentRepository documentRepository,
                                   AuditRepository auditRepository,
                                   RsaModularVerificationStrategy verificationStrategy,
                                   DocumentPreprocessorRegistry preprocessorRegistry,
                                   SignedEnvelopeFactory envelopeFactory,
                                   SignedDocumentEnvelopeService envelopeService) {
        this.identityClient = identityClient;
        this.documentRepository = documentRepository;
        this.auditRepository = auditRepository;
        this.verificationStrategy = verificationStrategy;
        this.preprocessorRegistry = preprocessorRegistry;
        this.envelopeFactory = envelopeFactory;
        this.envelopeService = envelopeService;
    }

    public SignedDocumentResponse sign(SignDocumentCommand command) {
        CitizenPrivateDto privateDto = identityClient.getPrivateKey(command.dni());
        CitizenPublicDto publicDto = identityClient.getPublicKey(command.dni());
        PreparedDocument prepared = preprocessorRegistry.prepare(command.fileName(), command.contentType(), command.content(), privateDto);

        String hashHex = crypto.sha256Hex(prepared.content());
        String signature = crypto.signToBase64(prepared.content(), codec.decodePrivate(privateDto.privateKeyBase64()));
        Instant signedAt = Instant.now();
        SignatureMetadata metadata = envelopeFactory.createMetadata(prepared, privateDto, publicDto, hashHex, signature, ALGORITHM, signedAt);
        byte[] signedPackageBytes = envelopeService.create(metadata, prepared.content());
        String signedFileName = envelopeFactory.signedFileName(prepared.fileName());
        String certificateJson = envelopeService.certificateJson(metadata);

        SignedDocumentRecord record = new SignedDocumentRecord(
                null,
                privateDto.dni(),
                privateDto.apellidosNombres(),
                privateDto.ubigeo(),
                prepared.fileName(),
                prepared.contentType(),
                prepared.content().length,
                prepared.content(),
                signature,
                hashHex,
                ALGORITHM,
                signedFileName,
                SignedDocumentEnvelopeService.SIGNED_MEDIA_TYPE,
                signedPackageBytes.length,
                signedPackageBytes,
                certificateJson,
                prepared.pdfStamped(),
                signedAt
        );
        Long id = documentRepository.save(record);
        auditRepository.save(new AuditRecord(null, "SIGN", privateDto.dni(), id, signedFileName, ALGORITHM, hashHex, true, signedAt));
        return new SignedDocumentResponse(
                id,
                privateDto.dni(),
                privateDto.apellidosNombres(),
                privateDto.ubigeo(),
                prepared.fileName(),
                signedFileName,
                prepared.contentType(),
                prepared.content().length,
                signedPackageBytes.length,
                "UNI-SIGNED-1.0: ZIP con documento + hash + firma + certificado embebido",
                prepared.pdfStamped(),
                ALGORITHM,
                hashHex,
                signature,
                metadata.certificate().issuer(),
                "/api/documentos/" + id + "/download-signed",
                signedAt
        );
    }

    public List<DocumentMetadataResponse> listByDni(String dni) {
        return documentRepository.findMetadataByDni(dni);
    }

    public SignedDocumentRecord findDocument(Long id) {
        return documentRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("Documento firmado no encontrado"));
    }

    public VerifyDocumentResponse verify(Long documentId) {
        SignedDocumentRecord doc = findDocument(documentId);
        VerifyDocumentResponse response = verifySignedPackage(doc.signedFileBytes(), "BD3", documentId, doc.signedFileName());
        auditRepository.save(new AuditRecord(null, "VERIFY_DB", response.dni(), doc.id(), doc.signedFileName(), response.algorithm(), response.hashHex(), response.valid(), Instant.now()));
        return response;
    }

    public VerifyDocumentResponse verifyUploaded(byte[] signedPackageBytes, String uploadedFileName) {
        VerifyDocumentResponse response = verifySignedPackage(signedPackageBytes, "UPLOAD", null, uploadedFileName);
        auditRepository.save(new AuditRecord(null, "VERIFY_UPLOAD", response.dni(), null, uploadedFileName, response.algorithm(), response.hashHex(), response.valid(), Instant.now()));
        return response;
    }

    private VerifyDocumentResponse verifySignedPackage(byte[] signedPackageBytes, String mode, Long documentId, String signedFileName) {
        SignedEnvelope envelope = envelopeService.read(signedPackageBytes);
        SignatureMetadata metadata = envelope.metadata();
        EmbeddedCertificate certificate = metadata.certificate();

        String calculatedHash = crypto.sha256Hex(envelope.payloadBytes());
        boolean hashValid = calculatedHash.equalsIgnoreCase(metadata.hashHex());
        boolean signatureValid = verificationStrategy.verify(envelope.payloadBytes(), metadata.signatureBase64(), codec.decodePublic(certificate.publicKeyBase64()));

        CitizenPublicDto trustedPublic = identityClient.getPublicKey(metadata.dni());
        boolean certificateTrusted = trustedPublic.publicKeyBase64().equals(certificate.publicKeyBase64())
                && trustedPublic.apellidosNombres().equals(metadata.apellidosNombres())
                && trustedPublic.ubigeo().equals(metadata.ubigeo());

        boolean valid = hashValid && signatureValid && certificateTrusted;
        String message = valid
                ? "Documento verificado: hash, firma y certificado coinciden."
                : invalidMessage(hashValid, signatureValid, certificateTrusted);

        return new VerifyDocumentResponse(
                documentId,
                metadata.dni(),
                metadata.apellidosNombres(),
                metadata.ubigeo(),
                metadata.originalFileName(),
                signedFileName,
                valid,
                hashValid,
                signatureValid,
                certificateTrusted,
                message,
                metadata.algorithm(),
                metadata.hashHex(),
                certificate.issuer(),
                metadata.signedAt(),
                mode
        );
    }

    private String invalidMessage(boolean hashValid, boolean signatureValid, boolean certificateTrusted) {
        StringBuilder sb = new StringBuilder("Documento no verificado:");
        if (!hashValid) sb.append(" el hash del documento no coincide;");
        if (!signatureValid) sb.append(" la firma RSA no corresponde al contenido;");
        if (!certificateTrusted) sb.append(" el certificado embebido no coincide con la Base de Datos 2;");
        return sb.toString();
    }

    public PayloadDownload visiblePayloadFromStoredDocument(Long id) {
        SignedDocumentRecord doc = findDocument(id);
        return new PayloadDownload(visibleFileName(doc.originalFileName(), doc.pdfStamped()), safeContentType(doc.contentType()), doc.documentBytes());
    }

    public PayloadDownload visiblePayloadFromUploadedPackage(byte[] signedPackageBytes) {
        SignedEnvelope envelope = envelopeService.read(signedPackageBytes);
        SignatureMetadata metadata = envelope.metadata();
        return new PayloadDownload(visibleFileName(metadata.originalFileName(), metadata.pdfStamped()), safeContentType(metadata.originalContentType()), envelope.payloadBytes());
    }

    public void deleteDocument(Long id) {
        findDocument(id);
        auditRepository.deleteByDocumentId(id);
        boolean deleted = documentRepository.deleteById(id);
        if (!deleted) {
            throw new IllegalArgumentException("Documento firmado no encontrado");
        }
    }

    public void deleteAudit(Long id) {
        boolean deleted = auditRepository.deleteById(id);
        if (!deleted) {
            throw new IllegalArgumentException("Auditoría no encontrada");
        }
    }

    private String safeContentType(String contentType) {
        return contentType == null || contentType.isBlank() ? "application/octet-stream" : contentType;
    }

    private String visibleFileName(String originalFileName, boolean pdfStamped) {
        String base = originalFileName == null || originalFileName.isBlank() ? "documento" : originalFileName;
        if (pdfStamped && base.toLowerCase().endsWith(".pdf")) {
            return base.substring(0, base.length() - 4) + "_sellado.pdf";
        }
        return base;
    }

    public List<AuditResponse> audits() {
        return auditRepository.findAll().stream().map(this::toAuditResponse).toList();
    }

    public AuditResponse auditById(Long id) {
        return auditRepository.findById(id).map(this::toAuditResponse).orElseThrow(() -> new IllegalArgumentException("Auditoría no encontrada"));
    }

    private AuditResponse toAuditResponse(AuditRecord r) {
        return new AuditResponse(r.id(), r.operation(), r.dni(), r.documentId(), r.fileName(), r.algorithm(), r.hashHex(), r.valid(), r.createdAt());
    }
}
