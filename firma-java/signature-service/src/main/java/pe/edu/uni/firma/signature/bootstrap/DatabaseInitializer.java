package pe.edu.uni.firma.signature.bootstrap;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.signature.repository.AuditRepository;
import pe.edu.uni.firma.signature.repository.SignedDocumentRepository;

@Component
public class DatabaseInitializer implements CommandLineRunner {
    private final SignedDocumentRepository documentRepository;
    private final AuditRepository auditRepository;

    public DatabaseInitializer(SignedDocumentRepository documentRepository, AuditRepository auditRepository) {
        this.documentRepository = documentRepository;
        this.auditRepository = auditRepository;
    }

    @Override
    public void run(String... args) {
        documentRepository.createTable();
        auditRepository.createTable();
    }
}
