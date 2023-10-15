import numpy as np


# Funkce pro simulaci provedení akce a získání odměny a následujícího stavu
def perform_action(state, action):
    # Tuto funkci upravte podle vaší aplikace, aby prováděla akci a vrátila odpovídající odměnu a následující stav
    # Například, pokud máte nějaký herní mechanismus, zde by mělo být zpracování pohybu a odezvy hry.
    # Pro jednoduchost v tomto příkladu předpokládáme, že stav je 0 a akce je 0 nebo 1 a odměna je 1, následující stav je 1.
    if state == 0:
        if action == 0:
            return 1, 1  # Akce 0 přechází z 0 do 1 s odměnou 1
        else:
            return 0, 0  # Akce 1 zůstává v 0 s odměnou 0
    else:
        # Pokud jste již ve stavu 1, můžete definovat podobně
        pass


# Počet stavů a akcí
num_states = 2
num_actions = 2

# Parametry učení
learning_rate = 0.1
discount_factor = 0.9
num_episodes = 1000

# Inicializace Q-tabulky
Q = np.zeros((num_states, num_actions))

# Simulace tréninku
for episode in range(num_episodes):
    # Počáteční stav (může být získán z odezvy hry)
    state = 0

    # Epizoda trvá, dokud nedosáhnete cíle nebo určitého stavu
    while state != 1:
        # Vyberte akci na základě epsilon-greedy strategie (například epsilon = 0.1)
        if np.random.rand() < 0.1:
            action = np.random.choice(num_actions)
        else:
            action = np.argmax(Q[state, :])

        # Simulace provedení akce a získání odměny a následujícího stavu (může být z odezvy hry)
        # V tomto příkladu používáme jednoduchou funkci, která vrací odměnu a následující stav
        reward, next_state = perform_action(state, action)

        # Aktualizace Q-hodnoty podle Bellmanovy rovnice
        Q[state, action] = Q[state, action] + learning_rate * (
                reward + discount_factor * np.max(Q[next_state, :]) - Q[state, action])

        # Přesun na následující stav
        state = next_state

# Konec tréninku, Q-tabulka by měla obsahovat naučené Q-hodnoty
print("Naučené Q-tabulky:")
print(Q)
