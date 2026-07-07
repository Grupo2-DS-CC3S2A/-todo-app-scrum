package pe.edu.uni.firma.identity.service;

import java.util.List;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.identity.domain.CitizenSeed;

/** Patrón Factory: genera los 15 ciudadanos de prueba solicitados. */
@Component
public class SeedCitizenFactory {
    public List<CitizenSeed> createDefaultCitizens() {
        return List.of(
            new CitizenSeed("45678901", "QUISPE HUAMAN, RENATO ALEXIS", "150101"),
            new CitizenSeed("45678902", "RAMOS FLORES, VALERIA ISABEL", "150102"),
            new CitizenSeed("45678903", "TORRES VARGAS, MARCO ANTONIO", "150103"),
            new CitizenSeed("45678904", "GARCIA CHAVEZ, LUCIA FERNANDA", "150104"),
            new CitizenSeed("45678905", "MENDOZA ROJAS, DIEGO ALONSO", "150105"),
            new CitizenSeed("45678906", "CASTILLO PAREDES, CAMILA SOFIA", "150106"),
            new CitizenSeed("45678907", "SALAZAR CORDOVA, ANDREA MILAGROS", "150107"),
            new CitizenSeed("45678908", "PEREZ AGUILAR, JORGE LUIS", "150108"),
            new CitizenSeed("45678909", "LOPEZ ARTEAGA, CESAR OMAR", "150109"),
            new CitizenSeed("45678910", "VILCHEZ NUNEZ, PAOLO EMILIO", "150110"),
            new CitizenSeed("45678911", "SANCHEZ MEDINA, ELENA PATRICIA", "150111"),
            new CitizenSeed("45678912", "RODRIGUEZ LEON, MATIAS ADRIAN", "150112"),
            new CitizenSeed("45678913", "FERNANDEZ DIAZ, NATALIA BELEN", "150113"),
            new CitizenSeed("45678914", "HUERTA CAMPOS, BRUNO SEBASTIAN", "150114"),
            new CitizenSeed("45678915", "MORALES ESPINOZA, CLAUDIA NOEMI", "150115")
        );
    }
}
