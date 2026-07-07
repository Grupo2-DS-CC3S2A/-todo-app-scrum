package pe.edu.uni.firma.identity.repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Optional;
import org.springframework.stereotype.Repository;
import pe.edu.uni.firma.identity.db.IdentityDbConnectionFactory;
import pe.edu.uni.firma.identity.dto.CitizenPrivateDto;

@Repository
public class PrivateCitizenKeyRepository {
    private final IdentityDbConnectionFactory connectionFactory;

    public PrivateCitizenKeyRepository(IdentityDbConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public void createTable() {
        executeUpdate("""
            CREATE TABLE IF NOT EXISTS private_citizen_keys (
                dni VARCHAR(8) PRIMARY KEY,
                apellidos_nombres VARCHAR(160) NOT NULL,
                ubigeo VARCHAR(6) NOT NULL,
                private_key_base64 CLOB NOT NULL
            )
            """);
    }

    public int count() {
        String sql = "SELECT COUNT(*) FROM private_citizen_keys";
        try (Connection cn = connectionFactory.privateConnection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            return rs.next() ? rs.getInt(1) : 0;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo contar registros de BD1 privada", ex);
        }
    }

    public void deleteAll() {
        executeUpdate("DELETE FROM private_citizen_keys");
    }

    public void save(CitizenPrivateDto dto) {
        String sql = """
            MERGE INTO private_citizen_keys(dni, apellidos_nombres, ubigeo, private_key_base64)
            KEY(dni) VALUES (?, ?, ?, ?)
            """;
        try (Connection cn = connectionFactory.privateConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, dto.dni());
            ps.setString(2, dto.apellidosNombres());
            ps.setString(3, dto.ubigeo());
            ps.setString(4, dto.privateKeyBase64());
            ps.executeUpdate();
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo guardar ciudadano en BD1 privada", ex);
        }
    }

    public Optional<CitizenPrivateDto> findByDni(String dni) {
        String sql = """
            SELECT dni, apellidos_nombres, ubigeo, private_key_base64
            FROM private_citizen_keys
            WHERE dni = ?
            """;
        try (Connection cn = connectionFactory.privateConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, dni);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }
                return Optional.of(new CitizenPrivateDto(
                        rs.getString("dni"),
                        rs.getString("apellidos_nombres"),
                        rs.getString("ubigeo"),
                        rs.getString("private_key_base64")
                ));
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo consultar ciudadano en BD1 privada", ex);
        }
    }

    private void executeUpdate(String sql) {
        try (Connection cn = connectionFactory.privateConnection();
             Statement st = cn.createStatement()) {
            st.executeUpdate(sql);
        } catch (SQLException ex) {
            throw new IllegalStateException("Error SQL en BD1 privada", ex);
        }
    }
}
