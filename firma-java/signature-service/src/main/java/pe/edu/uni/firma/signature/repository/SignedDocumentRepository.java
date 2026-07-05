package pe.edu.uni.firma.signature.repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Repository;
import pe.edu.uni.firma.signature.db.SignatureDbConnectionFactory;
import pe.edu.uni.firma.signature.domain.SignedDocumentRecord;
import pe.edu.uni.firma.signature.dto.DocumentMetadataResponse;

@Repository
public class SignedDocumentRepository {
    private final SignatureDbConnectionFactory connectionFactory;

    public SignedDocumentRepository(SignatureDbConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public void createTable() {
        executeUpdate("""
            CREATE TABLE IF NOT EXISTS signed_documents (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                dni VARCHAR(8) NOT NULL,
                apellidos_nombres VARCHAR(160) NOT NULL,
                ubigeo VARCHAR(6) NOT NULL,
                original_file_name VARCHAR(255) NOT NULL,
                content_type VARCHAR(120),
                file_size_bytes BIGINT NOT NULL,
                document_bytes BLOB NOT NULL,
                signature_base64 CLOB NOT NULL,
                hash_hex VARCHAR(64) NOT NULL,
                algorithm VARCHAR(120) NOT NULL,
                signed_file_name VARCHAR(255),
                signed_content_type VARCHAR(160),
                signed_file_size_bytes BIGINT,
                signed_file_bytes BLOB,
                certificate_json CLOB,
                pdf_stamped BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL
            )
            """);
        addColumnIfMissing("signed_file_name", "VARCHAR(255)");
        addColumnIfMissing("signed_content_type", "VARCHAR(160)");
        addColumnIfMissing("signed_file_size_bytes", "BIGINT");
        addColumnIfMissing("signed_file_bytes", "BLOB");
        addColumnIfMissing("certificate_json", "CLOB");
        addColumnIfMissing("pdf_stamped", "BOOLEAN DEFAULT FALSE");
    }

    public Long save(SignedDocumentRecord doc) {
        String sql = """
            INSERT INTO signed_documents(
                dni, apellidos_nombres, ubigeo, original_file_name, content_type,
                file_size_bytes, document_bytes, signature_base64, hash_hex, algorithm,
                signed_file_name, signed_content_type, signed_file_size_bytes, signed_file_bytes,
                certificate_json, pdf_stamped, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """;
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setString(1, doc.dni());
            ps.setString(2, doc.apellidosNombres());
            ps.setString(3, doc.ubigeo());
            ps.setString(4, doc.originalFileName());
            ps.setString(5, doc.contentType());
            ps.setLong(6, doc.fileSizeBytes());
            ps.setBytes(7, doc.documentBytes());
            ps.setString(8, doc.signatureBase64());
            ps.setString(9, doc.hashHex());
            ps.setString(10, doc.algorithm());
            ps.setString(11, doc.signedFileName());
            ps.setString(12, doc.signedContentType());
            ps.setLong(13, doc.signedFileSizeBytes());
            ps.setBytes(14, doc.signedFileBytes());
            ps.setString(15, doc.certificateJson());
            ps.setBoolean(16, doc.pdfStamped());
            ps.setTimestamp(17, Timestamp.from(doc.createdAt()));
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                return keys.next() ? keys.getLong(1) : null;
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo guardar documento firmado en BD3", ex);
        }
    }

    public List<DocumentMetadataResponse> findMetadataByDni(String dni) {
        String sql = """
            SELECT id, dni, original_file_name, signed_file_name, content_type,
                   file_size_bytes, signed_file_size_bytes, hash_hex, pdf_stamped, created_at
            FROM signed_documents WHERE dni = ? ORDER BY created_at DESC
            """;
        List<DocumentMetadataResponse> result = new ArrayList<>();
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, dni);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    result.add(new DocumentMetadataResponse(
                            rs.getLong("id"),
                            rs.getString("dni"),
                            rs.getString("original_file_name"),
                            rs.getString("signed_file_name"),
                            rs.getString("content_type"),
                            rs.getLong("file_size_bytes"),
                            rs.getLong("signed_file_size_bytes"),
                            rs.getString("hash_hex"),
                            rs.getBoolean("pdf_stamped"),
                            rs.getTimestamp("created_at").toInstant()
                    ));
                }
            }
            return result;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo listar documentos firmados por DNI", ex);
        }
    }

    public Optional<SignedDocumentRecord> findById(Long id) {
        String sql = "SELECT * FROM signed_documents WHERE id = ?";
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }
                return Optional.of(map(rs));
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo consultar documento firmado en BD3", ex);
        }
    }

    public boolean deleteById(Long id) {
        String sql = "DELETE FROM signed_documents WHERE id = ?";
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setLong(1, id);
            return ps.executeUpdate() > 0;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo eliminar documento firmado de BD3", ex);
        }
    }

    private SignedDocumentRecord map(ResultSet rs) throws SQLException {
        byte[] documentBytes = rs.getBytes("document_bytes");
        byte[] signedBytes = rs.getBytes("signed_file_bytes");
        return new SignedDocumentRecord(
                rs.getLong("id"),
                rs.getString("dni"),
                rs.getString("apellidos_nombres"),
                rs.getString("ubigeo"),
                rs.getString("original_file_name"),
                rs.getString("content_type"),
                rs.getLong("file_size_bytes"),
                documentBytes,
                rs.getString("signature_base64"),
                rs.getString("hash_hex"),
                rs.getString("algorithm"),
                rs.getString("signed_file_name"),
                rs.getString("signed_content_type"),
                rs.getLong("signed_file_size_bytes"),
                signedBytes,
                rs.getString("certificate_json"),
                rs.getBoolean("pdf_stamped"),
                rs.getTimestamp("created_at").toInstant()
        );
    }

    private void addColumnIfMissing(String name, String type) {
        try (Connection cn = connectionFactory.connection();
             ResultSet rs = cn.getMetaData().getColumns(null, null, "SIGNED_DOCUMENTS", name.toUpperCase())) {
            if (!rs.next()) {
                try (Statement st = cn.createStatement()) {
                    st.executeUpdate("ALTER TABLE signed_documents ADD COLUMN " + name + " " + type);
                }
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo migrar columna " + name + " en BD3", ex);
        }
    }

    private void executeUpdate(String sql) {
        try (Connection cn = connectionFactory.connection();
             Statement st = cn.createStatement()) {
            st.executeUpdate(sql);
        } catch (SQLException ex) {
            throw new IllegalStateException("Error SQL al inicializar BD3 documentos firmados", ex);
        }
    }
}
