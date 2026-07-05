package pe.edu.uni.firma.signature.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import pe.edu.uni.firma.signature.domain.SignedDocumentRecord;
import pe.edu.uni.firma.signature.dto.PayloadDownload;
import pe.edu.uni.firma.signature.dto.SignedDocumentResponse;

@Service
public class DocumentSignatureEmailService {

    private final JavaMailSender mailSender;
    private final String fromAddress;

    public DocumentSignatureEmailService(
            JavaMailSender mailSender,
            @Value("${app.mail.from:clopeza@uni.pe}") String fromAddress
    ) {
        this.mailSender = mailSender;
        this.fromAddress = fromAddress;
    }

    public void sendDocumentSubmittedEmail(
            String to,
            String dependencia,
            SignedDocumentResponse response,
            SignedDocumentRecord storedDocument,
            PayloadDownload visiblePayload
    ) {
        if (to == null || to.isBlank()) {
            throw new IllegalArgumentException("El correo del ciudadano es obligatorio para enviar la constancia.");
        }

        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setFrom(fromAddress);
            helper.setTo(to.trim());
            helper.setSubject("Documento Ingresado a Mesa de Partes Reniec");
            helper.setText(buildBody(dependencia, response), false);

            helper.addAttachment(
                    storedDocument.signedFileName(),
                    new ByteArrayResource(storedDocument.signedFileBytes())
            );

            helper.addAttachment(
                    visiblePayload.fileName(),
                    new ByteArrayResource(visiblePayload.bytes())
            );

            try {
                mailSender.send(message);
            } catch (Exception ex) {
            System.err.println("[signature-service] No se pudo enviar el correo: " + ex.getMessage());
            }
        } catch (MessagingException ex) {
            throw new IllegalStateException("No se pudo construir el correo de notificación.", ex);
        }
    }

    private String buildBody(String dependencia, SignedDocumentResponse response) {
        String dependenciaDestino = dependencia == null || dependencia.isBlank()
                ? "la dependencia seleccionada"
                : dependencia;

        return "Estimado(a) usuario(a),\n\n"
                + "Se ingresó correctamente su documento a la Mesa de Partes RENIEC.\n"
                + "El documento fue dirigido a la dependencia: " + dependenciaDestino + ".\n\n"
                + "En un plazo de 30 días se responderá por este mismo medio.\n\n"
                + "Datos de la firma digital:\n"
                + "DNI: " + response.dni() + "\n"
                + "Ciudadano: " + response.apellidosNombres() + "\n"
                + "Archivo original: " + response.originalFileName() + "\n"
                + "Hash: " + response.hashHex() + "\n\n"
                + "Se adjunta el contenedor firmado .uni-signed y el PDF con sello de firma.\n\n"
                + "Atentamente,\n"
                + "Mesa de Partes Virtual RENIEC";
    }
}
