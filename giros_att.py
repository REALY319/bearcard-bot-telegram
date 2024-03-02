import telebot
from telebot import types, util
import schedule
import time
from conexao_bot import conectar_mysql


# Função para aumentar a quantidade de todos os jogadores em 1
def aumentar_quantidade_jogadores():
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute("UPDATE jogadores SET qtdGiros = qtdGiros + 1;")
            conexao.commit()
            print("Quantidade de todos os jogadores aumentada em 1.")
        except Exception as e:
            print(f"Erro ao aumentar a quantidade de jogadores: {e}")
        finally:
            cursor.close()
            conexao.close()


# Agendar a função para ser executada a cada duas horas
schedule.every(1).hour.do(aumentar_quantidade_jogadores)

# Loop principal do bot
while True:
    try:
        # Verificar se há alguma tarefa agendada para ser executada
        schedule.run_pending()
        # Aguardar 1 segundo antes de verificar novamente
        time.sleep(1)
    except Exception as e:
        print(f"Ocorreu um erro no loop principal: {e}")
