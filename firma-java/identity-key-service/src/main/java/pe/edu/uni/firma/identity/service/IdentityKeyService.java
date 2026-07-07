package pe.edu.uni.firma.identity.service;

import java.util.List;

import org.springframework.stereotype.Service;

import pe.edu.uni.firma.common.crypto.KeyMaterialCodec;
import pe.edu.uni.firma.common.patterns.creational.KeyPairFactory.RsaKeyPairMaterial;
import pe.edu.uni.firma.common.patterns.creational.RsaKeyPairFactory;
import pe.edu.uni.firma.identity.dto.CitizenPrivateDto;
import pe.edu.uni.firma.identity.dto.CitizenPublicDto;
import pe.edu.uni.firma.identity.repository.SupabaseCitizenKeyRepository;
import pe.edu.uni.firma.identity.repository.SupabaseCitizenKeyRepository.CitizenRow;

@Service
public class IdentityKeyService {

    private final SupabaseCitizenKeyRepository repository;
    private final KeyMaterialCodec codec = new KeyMaterialCodec();
    private final RsaKeyPairFactory keyPairFactory = new RsaKeyPairFactory();

    public IdentityKeyService(SupabaseCitizenKeyRepository repository) {
        this.repository = repository;
    }

    public void initialize() {
        repository.ensureSchema();
    }

    public int seedKeysOnce() {
        repository.ensureSchema();

        if (repository.seedAlreadyExecuted()) {
            throw new IllegalStateException("Las llaves RSA ya fueron generadas anteriormente.");
        }

        List<CitizenRow> citizens = repository.findCitizensWithoutKeys();

        int total = 0;

        for (CitizenRow citizen : citizens) {
            RsaKeyPairMaterial keyPair = keyPairFactory.create();

            String privateKeyBase64 = codec.encodePrivate(keyPair.privateKey());
            String publicKeyBase64 = codec.encodePublic(keyPair.publicKey());

            repository.saveKeyPair(citizen, privateKeyBase64, publicKeyBase64);
            total++;
        }

        repository.markSeedExecuted(total);
        return total;
    }

    public List<CitizenPublicDto> listPublicCitizens() {
        return repository.findAllPublic();
    }

    public CitizenPublicDto findPublicByDni(String dni) {
        return repository.findPublicByDni(dni)
                .orElseThrow(() -> new IllegalArgumentException("DNI no existe en la base pública o no tiene llave pública."));
    }

    public CitizenPrivateDto findPrivateByDni(String dni) {
        return repository.findPrivateByDni(dni)
                .orElseThrow(() -> new IllegalArgumentException("DNI no existe en la base privada o no tiene llave privada."));
    }
}