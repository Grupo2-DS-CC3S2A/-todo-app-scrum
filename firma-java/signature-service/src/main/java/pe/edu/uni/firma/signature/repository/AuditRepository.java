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
import pe.edu.uni.firma.signature.domain.AuditRecord;

@Repository
public class AuditRepository {
    private final SignatureDbConnectionFactory connectionFactory;

    public AuditRepository(SignatureDbConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public void createTable() {
        executeUpdate("""
            CREATE TABLE IF NOT EXISTS signature_audit (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                operation VARCHAR(50) NOT NULL,
                dni VARCHAR(8) NOT NULL,
                document_id BIGINT,
                file_name VARCHAR(255),
                algorithm VARCHAR(80) NOT NULL,
                hash_hex VARCHAR(64) NOT NULL,
                valid BOOLEAN,
                created_at TIMESTAMP NOT NULL
            )
            """);
    }

    public void save(AuditRecord audit) {
        String sql = """
            INSERT INTO signature_audit(operation, dni, document_id, file_name, algorithm, hash_hex, valid, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """;
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, audit.operation());
            ps.setString(2, audit.dni());
            if (audit.documentId() == null) {
                ps.setObject(3, null);
            } else {
                ps.setLong(3, audit.documentId());
            }
            ps.setString(4, audit.fileName());
            ps.setString(5, audit.algorithm());
            ps.setString(6, audit.hashHex());
            if (audit.valid() == null) {
                ps.setObject(7, null);
            } else {
                ps.setBoolean(7, audit.valid());
            }
            ps.setTimestamp(8, Timestamp.from(audit.createdAt()));
            ps.executeUpdate();
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo guardar auditoría de firma", ex);
        }
    }

    public List<AuditRecord> findAll() {
        String sql = "SELECT * FROM signature_audit ORDER BY created_at DESC";
        List<AuditRecord> result = new ArrayList<>();
        try (Connection cn = connectionFactory.connection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            while (rs.next()) {
                result.add(map(rs));
            }
            return result;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo listar auditoría", ex);
        }
    }

    public Optional<AuditRecord> findById(Long id) {
        String sql = "SELECT * FROM signature_audit WHERE id = ?";
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? Optional.of(map(rs)) : Optional.empty();
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo consultar auditoría por id", ex);
        }
    }

    public boolean deleteById(Long id) {
        String sql = "DELETE FROM signature_audit WHERE id = ?";
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setLong(1, id);
            return ps.executeUpdate() > 0;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo eliminar registro de auditoría", ex);
        }
    }

    public int deleteByDocumentId(Long documentId) {
        String sql = "DELETE FROM signature_audit WHERE document_id = ?";
        try (Connection cn = connectionFactory.connection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setLong(1, documentId);
            return ps.executeUpdate();
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo eliminar auditoría asociada al documento", ex);
        }
    }

    private AuditRecord map(ResultSet rs) throws SQLException {
        return new AuditRecord(
                rs.getLong("id"),
                rs.getString("operation"),
                rs.getString("dni"),
                rs.getObject("document_id") == null ? null : rs.getLong("document_id"),
                rs.getString("file_name"),
                rs.getString("algorithm"),
                rs.getString("hash_hex"),
                rs.getObject("valid") == null ? null : rs.getBoolean("valid"),
                rs.getTimestamp("created_at").toInstant()
        );
    }

    private void executeUpdate(String sql) {
        try (Connection cn = connectionFactory.connection();
             Statement st = cn.createStatement()) {
            st.executeUpdate(sql);
        } catch (SQLException ex) {
            throw new IllegalStateException("Error SQL al inicializar auditoría", ex);
        }
    }
}
