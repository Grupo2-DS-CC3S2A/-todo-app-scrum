package pe.edu.uni.firma.identity.repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Repository;
import pe.edu.uni.firma.identity.db.IdentityDbConnectionFactory;
import pe.edu.uni.firma.identity.dto.CitizenPublicDto;

@Repository
public class PublicCitizenKeyRepository {
    private final IdentityDbConnectionFactory connectionFactory;

    public PublicCitizenKeyRepository(IdentityDbConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public void createTable() {
        executeUpdate("""
            CREATE TABLE IF NOT EXISTS public_citizen_keys (
                dni VARCHAR(8) PRIMARY KEY,
                apellidos_nombres VARCHAR(160) NOT NULL,
                ubigeo VARCHAR(6) NOT NULL,
                public_key_base64 CLOB NOT NULL
            )
            """);
    }

    public int count() {
        String sql = "SELECT COUNT(*) FROM public_citizen_keys";
        try (Connection cn = connectionFactory.publicConnection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            return rs.next() ? rs.getInt(1) : 0;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo contar registros de BD2 pública", ex);
        }
    }

    public void deleteAll() {
        executeUpdate("DELETE FROM public_citizen_keys");
    }

    public void save(CitizenPublicDto dto) {
        String sql = """
            MERGE INTO public_citizen_keys(dni, apellidos_nombres, ubigeo, public_key_base64)
            KEY(dni) VALUES (?, ?, ?, ?)
            """;
        try (Connection cn = connectionFactory.publicConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, dto.dni());
            ps.setString(2, dto.apellidosNombres());
            ps.setString(3, dto.ubigeo());
            ps.setString(4, dto.publicKeyBase64());
            ps.executeUpdate();
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo guardar ciudadano en BD2 pública", ex);
        }
    }

    public Optional<CitizenPublicDto> findByDni(String dni) {
        String sql = """
            SELECT dni, apellidos_nombres, ubigeo, public_key_base64
            FROM public_citizen_keys
            WHERE dni = ?
            """;
        try (Connection cn = connectionFactory.publicConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {
            ps.setString(1, dni);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }
                return Optional.of(new CitizenPublicDto(
                        rs.getString("dni"),
                        rs.getString("apellidos_nombres"),
                        rs.getString("ubigeo"),
                        rs.getString("public_key_base64")
                ));
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo consultar ciudadano en BD2 pública", ex);
        }
    }

    public List<CitizenPublicDto> findAll() {
        String sql = """
            SELECT dni, apellidos_nombres, ubigeo, public_key_base64
            FROM public_citizen_keys
            ORDER BY apellidos_nombres
            """;
        List<CitizenPublicDto> result = new ArrayList<>();
        try (Connection cn = connectionFactory.publicConnection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            while (rs.next()) {
                result.add(new CitizenPublicDto(
                        rs.getString("dni"),
                        rs.getString("apellidos_nombres"),
                        rs.getString("ubigeo"),
                        rs.getString("public_key_base64")
                ));
            }
            return result;
        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo listar ciudadanos de BD2 pública", ex);
        }
    }

    private void executeUpdate(String sql) {
        try (Connection cn = connectionFactory.publicConnection();
             Statement st = cn.createStatement()) {
            st.executeUpdate(sql);
        } catch (SQLException ex) {
            throw new IllegalStateException("Error SQL en BD2 pública", ex);
        }
    }
}
