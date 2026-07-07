package pe.edu.uni.firma.signature.container;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.springframework.stereotype.Component;

/**
 * Contenedor firmado UNI.
 * Patrón estructural: Encapsulation/Facade de empaquetado criptográfico.
 */
@Component
public class SignedDocumentEnvelopeService {
    public static final String SIGNED_MEDIA_TYPE = "application/vnd.uni.signed-document+zip";
    public static final String METADATA_ENTRY = "META-INF/uni-signature.json";
    public static final String CERTIFICATE_ENTRY = "META-INF/uni-certificate.json";
    public static final String README_ENTRY = "README.txt";

    private final ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);

    public byte[] create(SignatureMetadata metadata, byte[] payloadBytes) {
        Objects.requireNonNull(metadata, "metadata");
        Objects.requireNonNull(payloadBytes, "payloadBytes");
        try (ByteArrayOutputStream bos = new ByteArrayOutputStream();
             ZipOutputStream zos = new ZipOutputStream(bos, StandardCharsets.UTF_8)) {
            writeEntry(zos, metadata.payloadEntryName(), payloadBytes);
            writeEntry(zos, METADATA_ENTRY, mapper.writeValueAsBytes(metadata));
            writeEntry(zos, CERTIFICATE_ENTRY, mapper.writeValueAsBytes(metadata.certificate()));
            writeEntry(zos, README_ENTRY, readme(metadata).getBytes(StandardCharsets.UTF_8));
            zos.finish();
            return bos.toByteArray();
        } catch (IOException ex) {
            throw new IllegalStateException("No se pudo crear el contenedor firmado UNI", ex);
        }
    }

    public SignedEnvelope read(byte[] signedPackageBytes) {
        Objects.requireNonNull(signedPackageBytes, "signedPackageBytes");
        SignatureMetadata metadata = null;
        byte[] payloadBytes = null;
        String payloadName = null;

        try (ZipInputStream zis = new ZipInputStream(new ByteArrayInputStream(signedPackageBytes), StandardCharsets.UTF_8)) {
            ZipEntry entry;
            while ((entry = zis.getNextEntry()) != null) {
                byte[] data = zis.readAllBytes();
                if (METADATA_ENTRY.equals(entry.getName())) {
                    metadata = mapper.readValue(data, SignatureMetadata.class);
                } else if (entry.getName().startsWith("payload/") && !entry.isDirectory()) {
                    payloadName = entry.getName();
                    payloadBytes = data;
                }
            }
        } catch (IOException ex) {
            throw new IllegalArgumentException("El archivo firmado no es un contenedor UNI válido", ex);
        }

        if (metadata == null) {
            throw new IllegalArgumentException("El contenedor no incluye META-INF/uni-signature.json");
        }
        if (payloadBytes == null) {
            throw new IllegalArgumentException("El contenedor no incluye el documento encapsulado");
        }
        if (!metadata.payloadEntryName().equals(payloadName)) {
            throw new IllegalArgumentException("El documento encapsulado no coincide con la metadata de firma");
        }
        return new SignedEnvelope(metadata, payloadBytes);
    }

    public String certificateJson(SignatureMetadata metadata) {
        try {
            return mapper.writeValueAsString(metadata.certificate());
        } catch (IOException ex) {
            throw new IllegalStateException("No se pudo serializar el certificado embebido", ex);
        }
    }

    private void writeEntry(ZipOutputStream zos, String name, byte[] data) throws IOException {
        ZipEntry entry = new ZipEntry(name);
        zos.putNextEntry(entry);
        zos.write(data);
        zos.closeEntry();
    }

    private String readme(SignatureMetadata metadata) {
        return "Archivo firmado digitalmente por el Servicio de Firma Digital UNI\n"
                + "Formato: contenedor .uni-signed\n"
                + "DNI firmante: " + metadata.dni() + "\n"
                + "Firmante: " + metadata.apellidosNombres() + "\n"
                + "Documento original: " + metadata.originalFileName() + "\n"
                + "Algoritmo: " + metadata.algorithm() + "\n"
                + "Hash SHA-256: " + metadata.hashHex() + "\n"
                + "Fecha de firma: " + metadata.signedAt() + "\n"
                + "\nEl contenedor incluye el documento, la firma digital, el hash y el certificado lógico del firmante.\n";
    }
}
