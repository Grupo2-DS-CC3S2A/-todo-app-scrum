package pe.edu.uni.firma.identity.repository;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.springframework.stereotype.Repository;

import pe.edu.uni.firma.identity.db.IdentityDbConnectionFactory;
import pe.edu.uni.firma.identity.dto.CitizenPrivateDto;
import pe.edu.uni.firma.identity.dto.CitizenPublicDto;

@Repository
public class SupabaseCitizenKeyRepository {

    private final IdentityDbConnectionFactory connectionFactory;

    public SupabaseCitizenKeyRepository(IdentityDbConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    public void ensureSchema() {
        try (Connection cn = connectionFactory.privateConnection();
             Statement st = cn.createStatement()) {

            st.executeUpdate("""
                ALTER TABLE public.citizens
                ADD COLUMN IF NOT EXISTS llave_privada TEXT
                """);

            st.executeUpdate("""
                CREATE SCHEMA IF NOT EXISTS firma_publica
                """);

            st.executeUpdate("""
                CREATE TABLE IF NOT EXISTS firma_publica.citizens (
                    dni VARCHAR(8) PRIMARY KEY,
                    digit INTEGER NOT NULL,
                    issue_date DATE NOT NULL,
                    firstname VARCHAR NOT NULL,
                    lastname VARCHAR NOT NULL,
                    llave_publica TEXT
                )
                """);

            st.executeUpdate("""
                INSERT INTO firma_publica.citizens (
                    dni,
                    digit,
                    issue_date,
                    firstname,
                    lastname,
                    llave_publica
                )
                SELECT
                    dni,
                    digit,
                    issue_date,
                    firstname,
                    lastname,
                    NULL
                FROM public.citizens
                ON CONFLICT (dni) DO NOTHING
                """);

            st.executeUpdate("""
                CREATE TABLE IF NOT EXISTS public.key_seed_control (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
                    total_keys INTEGER NOT NULL,
                    CONSTRAINT only_one_seed CHECK (id = 1)
                )
                """);

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo preparar Supabase para llaves RSA.", ex);
        }
    }

    public boolean seedAlreadyExecuted() {
        String sql = "SELECT COUNT(*) FROM public.key_seed_control WHERE id = 1";

        try (Connection cn = connectionFactory.privateConnection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {

            return rs.next() && rs.getInt(1) > 0;

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo verificar key_seed_control.", ex);
        }
    }

    public List<CitizenRow> findCitizensWithoutKeys() {
        String sql = """
            SELECT
                c.dni,
                c.digit,
                c.issue_date,
                c.firstname,
                c.lastname
            FROM public.citizens c
            LEFT JOIN firma_publica.citizens p ON p.dni = c.dni
            WHERE c.llave_privada IS NULL
               OR p.llave_publica IS NULL
            ORDER BY c.dni
            """;

        List<CitizenRow> citizens = new ArrayList<>();

        try (Connection cn = connectionFactory.privateConnection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {

            while (rs.next()) {
                citizens.add(new CitizenRow(
                        rs.getString("dni"),
                        rs.getInt("digit"),
                        rs.getDate("issue_date"),
                        rs.getString("firstname"),
                        rs.getString("lastname")
                ));
            }

            return citizens;

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo leer ciudadanos sin llaves.", ex);
        }
    }

    public void saveKeyPair(CitizenRow citizen, String privateKeyBase64, String publicKeyBase64) {
        String updatePrivate = """
            UPDATE public.citizens
            SET llave_privada = ?
            WHERE dni = ?
            """;

        String upsertPublic = """
            INSERT INTO firma_publica.citizens (
                dni,
                digit,
                issue_date,
                firstname,
                lastname,
                llave_publica
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (dni) DO UPDATE
            SET
                digit = EXCLUDED.digit,
                issue_date = EXCLUDED.issue_date,
                firstname = EXCLUDED.firstname,
                lastname = EXCLUDED.lastname,
                llave_publica = EXCLUDED.llave_publica
            """;

        try (Connection cn = connectionFactory.privateConnection()) {
            cn.setAutoCommit(false);

            try (
                    PreparedStatement psPrivate = cn.prepareStatement(updatePrivate);
                    PreparedStatement psPublic = cn.prepareStatement(upsertPublic)
            ) {
                psPrivate.setString(1, privateKeyBase64);
                psPrivate.setString(2, citizen.dni());
                psPrivate.executeUpdate();

                psPublic.setString(1, citizen.dni());
                psPublic.setInt(2, citizen.digit());
                psPublic.setDate(3, citizen.issueDate());
                psPublic.setString(4, citizen.firstname());
                psPublic.setString(5, citizen.lastname());
                psPublic.setString(6, publicKeyBase64);
                psPublic.executeUpdate();

                cn.commit();

            } catch (Exception ex) {
                cn.rollback();
                throw ex;
            }

        } catch (Exception ex) {
            throw new IllegalStateException("No se pudo guardar par RSA para DNI " + citizen.dni(), ex);
        }
    }

    public void markSeedExecuted(int totalKeys) {
        String sql = """
            INSERT INTO public.key_seed_control (id, total_keys)
            VALUES (1, ?)
            ON CONFLICT (id) DO NOTHING
            """;

        try (Connection cn = connectionFactory.privateConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {

            ps.setInt(1, totalKeys);
            ps.executeUpdate();

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo registrar ejecución única de llaves.", ex);
        }
    }

    public Optional<CitizenPrivateDto> findPrivateByDni(String dni) {
        String sql = """
            SELECT
                dni,
                firstname,
                lastname,
                llave_privada
            FROM public.citizens
            WHERE dni = ?
              AND llave_privada IS NOT NULL
            """;

        try (Connection cn = connectionFactory.privateConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {

            ps.setString(1, dni);

            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }

                String apellidosNombres = rs.getString("firstname") + " " + rs.getString("lastname");

                return Optional.of(new CitizenPrivateDto(
                        rs.getString("dni"),
                        apellidosNombres,
                        "000000",
                        rs.getString("llave_privada")
                ));
            }

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo consultar llave privada.", ex);
        }
    }

    public Optional<CitizenPublicDto> findPublicByDni(String dni) {
        String sql = """
            SELECT
                dni,
                firstname,
                lastname,
                llave_publica
            FROM firma_publica.citizens
            WHERE dni = ?
              AND llave_publica IS NOT NULL
            """;

        try (Connection cn = connectionFactory.publicConnection();
             PreparedStatement ps = cn.prepareStatement(sql)) {

            ps.setString(1, dni);

            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }

                String apellidosNombres = rs.getString("firstname") + " " + rs.getString("lastname");

                return Optional.of(new CitizenPublicDto(
                        rs.getString("dni"),
                        apellidosNombres,
                        "000000",
                        rs.getString("llave_publica")
                ));
            }

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo consultar llave pública.", ex);
        }
    }

    public List<CitizenPublicDto> findAllPublic() {
        String sql = """
            SELECT
                dni,
                firstname,
                lastname,
                llave_publica
            FROM firma_publica.citizens
            WHERE llave_publica IS NOT NULL
            ORDER BY firstname, lastname
            """;

        List<CitizenPublicDto> result = new ArrayList<>();

        try (Connection cn = connectionFactory.publicConnection();
             Statement st = cn.createStatement();
             ResultSet rs = st.executeQuery(sql)) {

            while (rs.next()) {
                String apellidosNombres = rs.getString("firstname") + " " + rs.getString("lastname");

                result.add(new CitizenPublicDto(
                        rs.getString("dni"),
                        apellidosNombres,
                        "000000",
                        rs.getString("llave_publica")
                ));
            }

            return result;

        } catch (SQLException ex) {
            throw new IllegalStateException("No se pudo listar ciudadanos públicos.", ex);
        }
    }

    public record CitizenRow(
            String dni,
            int digit,
            Date issueDate,
            String firstname,
            String lastname
    ) {
    }
}