package pe.edu.uni.firma.identity.bootstrap;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.identity.service.IdentityKeyService;

@Component
public class DatabaseSeeder implements CommandLineRunner {
    private final IdentityKeyService service;

    public DatabaseSeeder(IdentityKeyService service) {
        this.service = service;
    }

    @Override
    public void run(String... args) {
        service.initialize();
    }
}
