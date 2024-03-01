import telebot
from telebot import types, util
from conexao_bot import conectar_mysql
from threading import Thread
import random

bot = telebot.TeleBot("token")

# Dicionário para armazenar informações sobre os jogadores
jogadores_registrados = {}


@bot.message_handler(commands=["spin", "start", "help"])
def restricted_commands(message):
    chat_id = message.chat.id
    if chat_id > 0:  # Verifica se é um chat privado
        if message.text.startswith("/spin"):
            spin_command(message)
        elif message.text.startswith("/start"):
            start_command(message)
        elif message.text.startswith("/help"):
            help_command(message)
    else:
        bot.send_message(chat_id, "Esses comandos não podem ser executados em grupos.")


def obter_cartas_unicas_jogador_por_obra(user_id, obra_nome):
    # Suponha que você tenha uma função que retorna todas as cartas do jogador para uma obra
    cartas_jogador_obra = obter_cartas_jogador_por_obra(user_id, obra_nome)

    # Lista para armazenar cartas únicas
    cartas_unicas = []

    for carta in cartas_jogador_obra:
        # Verifica se a carta já está na lista de cartas únicas
        if carta not in cartas_unicas:
            cartas_unicas.append(carta)

    return cartas_unicas


def atualizar_qtd_tiradas_carta(carta_id):
    conexao = conectar_mysql()

    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"UPDATE cartas SET qtdTiradas = qtdTiradas + 1 WHERE cartaId = {carta_id}"
            )
            conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar quantidade de tiradas da carta: {e}")
        finally:
            cursor.close()
            conexao.close()


emojis_por_categoria = {
    "GamerBear": "🕹️",
    "DJBear": "🎧",
    "CineBear": "🍿",
    "OtakuBear": "🇯🇵",
    "LeitorBear": "📚",
    "EsporteBear": "🏀",
}


# Adicione esta função no seu código
def obter_categoria_da_obra(obra_nome):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT categoriaNome FROM obras WHERE obraNome = '{obra_nome}' LIMIT 1"
            )
            categoria = cursor.fetchone()
            return categoria[0] if categoria else None
        except Exception as e:
            print(f"Erro ao obter categoria da obra: {e}")
        finally:
            cursor.close()
            conexao.close()

    return None


def obter_nome_obra_por_input(obra_input):
    conexao = conectar_mysql()
    obra_nome = None

    if conexao:
        try:
            cursor = conexao.cursor()
            # Verifica se o input corresponde ao nome da obra
            cursor.execute(
                f"SELECT obraNome FROM obras WHERE obraNome = %s", (obra_input,)
            )
            obra_nome = cursor.fetchone()

            if obra_nome:
                return obra_nome[0]

            # Verifica se o input corresponde ao apelido da obra
            cursor.execute(
                f"SELECT obraNome FROM obras WHERE obraApelido = %s", (obra_input,)
            )
            obra_nome = cursor.fetchone()

            if obra_nome:
                return obra_nome[0]
        except Exception as e:
            print(f"Erro ao obter nome da obra por input: {e}")
        finally:
            cursor.close()
            conexao.close()

    return None


def obter_total_cartas_obra(obra_nome):
    conexao = conectar_mysql()
    total_cartas = 0

    if conexao:
        try:
            cursor = conexao.cursor()
            # Obtém o número total de cartas na obra
            cursor.execute(
                "SELECT COUNT(*) FROM cartas WHERE obraNome = %s", (obra_nome,)
            )
            total_cartas = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao obter total de cartas da obra: {e}")
        finally:
            cursor.close()
            conexao.close()

    return total_cartas


def obter_cartas_jogador_por_obra(user_id, obra_nome):
    conexao = conectar_mysql()
    cartas_jogador_obra = []

    if conexao:
        try:
            cursor = conexao.cursor()
            # Obtém as cartas do jogador na obra especificada
            cursor.execute(
                f"SELECT cartaId, categoriaNome, obraNome, cartaNome, cartaImagem FROM cartas_jogadores WHERE jogadorId = {user_id} AND obraNome = %s ORDER BY categoriaNome, cartaNome",
                (obra_nome,),
            )
            cartas_jogador_obra = cursor.fetchall()
        except Exception as e:
            print(f"Erro ao obter cartas do jogador na obra: {e}")
        finally:
            cursor.close()
            conexao.close()

    return cartas_jogador_obra


def obter_imagem_obra(obra_nome):
    conexao = conectar_mysql()
    imagem_obra = None

    if conexao:
        try:
            cursor = conexao.cursor()
            # Obtém a URL da imagem da obra
            cursor.execute(
                "SELECT obraImagem FROM obras WHERE obraNome = %s", (obra_nome,)
            )
            imagem_obra = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao obter imagem da obra: {e}")
        finally:
            cursor.close()
            conexao.close()

    return imagem_obra


def obter_cartas_faltantes_obra(user_id, obra_nome):
    conexao = conectar_mysql()
    cartas_faltantes = []

    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)

            # Obtém todas as cartas da obra
            cursor.execute(
                "SELECT cartaId, cartaNome FROM cartas WHERE obraNome = %s",
                (obra_nome,),
            )
            cartas_obra = {
                carta["cartaId"]: carta["cartaNome"] for carta in cursor.fetchall()
            }

            # Obtém as cartas do jogador na obra
            cursor.execute(
                "SELECT cartaId, cartaNome FROM cartas_jogadores WHERE jogadorId = %s AND obraNome = %s",
                (user_id, obra_nome),
            )
            cartas_jogador = {
                carta["cartaId"]: carta["cartaNome"] for carta in cursor.fetchall()
            }

            # Encontra as cartas que o jogador ainda não possui
            cartas_faltantes = [
                (carta_id, nome_da_carta)
                for carta_id, nome_da_carta in cartas_obra.items()
                if carta_id not in cartas_jogador
            ]

        except Exception as e:
            print(f"Erro ao obter cartas faltantes para a obra: {e}")
        finally:
            cursor.close()
            conexao.close()

    return cartas_faltantes


def obter_obras_por_categoria():
    conexao = conectar_mysql()
    obras_por_categoria = {}

    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT categoriaNome, obraNome FROM obras ORDER BY categoriaNome, obraNome;"
            )
            obras = cursor.fetchall()

            for obra in obras:
                categoria = obra["categoriaNome"]
                nome = obra["obraNome"]

                if categoria not in obras_por_categoria:
                    obras_por_categoria[categoria] = []

                obras_por_categoria[categoria].append(nome)

        except Exception as e:
            print(f"Erro ao obter obras por categoria do banco de dados: {e}")
        finally:
            cursor.close()
            conexao.close()

    return obras_por_categoria


# Comando /obras para mostrar todas as obras
@bot.message_handler(commands=["obras"])
def obras_command(message):
    chat_id = message.chat.id

    # Conecte-se ao banco de dados e recupere as obras por categoria
    obras_por_categoria = obter_obras_por_categoria()

    if obras_por_categoria:
        # Crie a mensagem com as obras separadas por categorias
        mensagem_obras = "Aqui estão as obras separadas por categorias:\n\n"

        for categoria, obras in obras_por_categoria.items():
            mensagem_obras += f"<b>{categoria}:</b>\n"
            for obra in obras:
                mensagem_obras += f" - {obra}\n"
            mensagem_obras += "\n"

        # Envie a mensagem formatada
        bot.send_message(chat_id, mensagem_obras, parse_mode="HTML")
    else:
        bot.send_message(chat_id, "Não há obras cadastradas no momento.")


@bot.message_handler(commands=["have"])
def have_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Obtém o input do usuário após o comando
    input_args = message.text.split(" ", 1)
    if len(input_args) != 2:
        bot.send_message(
            chat_id, "Formato inválido. Use /have <nome_ou_apelido_da_obra>"
        )
        return

    obra_input = input_args[1].strip()

    # Obtém o nome da obra correspondente ao input do usuário
    obra_nome = obter_nome_obra_por_input(obra_input)

    if obra_nome:
        # Obtém as cartas únicas do jogador na obra
        cartas_jogador_obra_unicas = obter_cartas_unicas_jogador_por_obra(
            user_id, obra_nome
        )

        if cartas_jogador_obra_unicas:
            # Obtém o total de cartas na obra
            total_cartas_obra = obter_total_cartas_obra(obra_nome)

            # Obtém o emoji da categoria da obra
            categoria_emoji = emojis_por_categoria.get(
                obter_categoria_da_obra(obra_nome), "❓"
            )

            # Obtém a URL da imagem da obra
            imagem_obra = obter_imagem_obra(obra_nome)

            # Menciona a mensagem original
            reply_to_message_id = message.message_id

            # Cria a mensagem com as cartas do jogador na obra
            mensagem_colecao = f" ✅ | <b>{obra_nome}</b> \n📁 | {len(cartas_jogador_obra_unicas)}/{total_cartas_obra} \n"

            for carta in cartas_jogador_obra_unicas:
                carta_id, categoria_nome, obra_nome, nome_da_carta, _ = carta

                # Adiciona o emoji da categoria à mensagem
                mensagem_colecao += f"\n {categoria_emoji} <code>{carta_id}</code>. <b>{nome_da_carta}</b>"

            # Se o jogador possui todas as cartas, envie uma mensagem específica
            if len(cartas_jogador_obra_unicas) == total_cartas_obra:
                mensagem_colecao += (
                    "\n\nParabéns! Você completou a coleção para esta obra."
                )
                # Envia a mensagem ao jogador com a imagem da obra
                bot.send_photo(
                    chat_id,
                    imagem_obra,
                    caption=mensagem_colecao,
                    parse_mode="HTML",
                    reply_to_message_id=reply_to_message_id,
                )
            else:
                # Envia a mensagem ao jogador com a imagem da obra
                bot.send_photo(
                    chat_id,
                    imagem_obra,
                    caption=mensagem_colecao,
                    parse_mode="HTML",
                    reply_to_message_id=reply_to_message_id,
                )
        else:
            bot.send_message(
                chat_id, f"Você não possui cartas para a obra '{obra_nome}'."
            )
    else:
        bot.send_message(chat_id, "Obra não encontrada. Verifique o nome ou apelido.")


@bot.message_handler(commands=["nhave"])
def nhave_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Obtém o input do usuário após o comando
    input_args = message.text.split(" ", 1)
    if len(input_args) != 2:
        bot.send_message(
            chat_id, "Formato inválido. Use /nhave <nome_ou_apelido_da_obra>"
        )
        return

    obra_input = input_args[1].strip()

    # Obtém o nome da obra correspondente ao input do usuário
    obra_nome = obter_nome_obra_por_input(obra_input)

    if obra_nome:
        # Obtém as cartas do jogador na obra
        cartas_jogador_obra = obter_cartas_jogador_por_obra(user_id, obra_nome)

        # Obtém o total de cartas na obra
        total_cartas_obra = obter_total_cartas_obra(obra_nome)

        # Obtém as cartas que o jogador não possui na obra
        cartas_faltantes = obter_cartas_faltantes_obra(user_id, obra_nome)

        # Obtém o emoji da categoria da obra
        categoria_emoji = emojis_por_categoria.get(
            obter_categoria_da_obra(obra_nome), "❓"
        )

        # Obtém a URL da imagem da obra
        imagem_obra = obter_imagem_obra(obra_nome)

        # Menciona a mensagem original
        reply_to_message_id = message.message_id

        # Cria a mensagem com as cartas que faltam para o jogador completar a obra
        mensagem_colecao = f" ❌ | <b>{obra_nome}</b> \n📁 | {len(cartas_faltantes)}/{total_cartas_obra} \n"

        if cartas_faltantes:
            for carta in cartas_faltantes:
                carta_id, nome_da_carta = carta

                # Adiciona o emoji da categoria à mensagem
                mensagem_colecao += f"\n {categoria_emoji} <code>{carta_id}</code>. <b>{nome_da_carta}</b>"
        else:
            # Se o jogador não tem nenhuma carta, mostra todas as cartas necessárias
            for i in range(1, total_cartas_obra + 1):
                # Adiciona o emoji da categoria à mensagem
                mensagem_colecao += (
                    f"\n {categoria_emoji} <code>{i}</code>. <i>(Carta não obtida)</i>"
                )

        # Envia a mensagem ao jogador com a imagem da obra
        bot.send_photo(
            chat_id,
            imagem_obra,
            caption=mensagem_colecao,
            parse_mode="HTML",
            reply_to_message_id=reply_to_message_id,
        )
    else:
        bot.send_message(chat_id, "Obra não encontrada. Verifique o nome ou apelido.")


def obter_qtd_tiradas_carta(carta_id):
    conexao = conectar_mysql()
    qtd_tiradas = 0

    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT qtdTiradas FROM cartas WHERE cartaId = %s", (carta_id,)
            )
            qtd_tiradas = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao obter quantidade de tiradas da carta: {e}")
        finally:
            cursor.close()
            conexao.close()

    return qtd_tiradas


@bot.message_handler(commands=["id"])
def id_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Obtém o ID da carta da mensagem
    try:
        carta_id = message.text
        # Replace na mensagem, para pegar somente id
        replace_carta = carta_id.replace("/id ", "")
        carta_id = int(replace_carta)

    except ValueError:
        bot.send_message(chat_id, "Formato de ID inválido.")
        return

    print(f"ID da carta obtido: {carta_id}")

    # Obtém as informações da carta usando o ID
    carta_info = obter_carta_por_id(carta_id)

    print(f"Retorno de obter_carta_por_id: {carta_info}")

    # Obtém a quantidade de tiradas da carta
    qtd_tiradas = obter_qtd_tiradas_carta(carta_id)

    print(f"Quantidade de tiradas: {qtd_tiradas}")

    # Menciona a mensagem original
    reply_to_message_id = message.message_id

    if carta_info:
        nome_da_carta = carta_info["cartaNome"]
        obra_nome = carta_info["obraNome"]
        categoria_nome = carta_info["categoriaNome"]
        link_imagem = carta_info["cartaImagem"]
        emojis_por_categoria = {
            "GamerBear": "🕹️",
            "DJBear": "🎧",
            "CineBear": "🍿",
            "OtakuBear": "🇯🇵",
            "LeitorBear": "📚",
            "EsporteBear": "🏀",
        }

        # Cria a mensagem com informações da carta
        mensagem = (
            f"{emojis_por_categoria.get(categoria_nome, '')} <code>{carta_id}</code>. <b>{nome_da_carta}</b>\n"
            f"<i>{obra_nome}</i>\n\n"
            f"🎰: {qtd_tiradas} vez(es) tirada"
        )

        # Envia a imagem da carta com informações
        bot.send_photo(
            chat_id,
            link_imagem,
            caption=mensagem,
            parse_mode="HTML",
            reply_to_message_id=reply_to_message_id,
        )
    else:
        bot.send_message(chat_id, "ID de carta não encontrado.")


def is_valid_username(username):
    # Verifica se o nome de usuário não está vazio e tem comprimento entre 5 e 32 caracteres
    return bool(username) and 5 <= len(username) <= 32


@bot.message_handler(commands=["user"])
def user_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Obtém o novo username da mensagem
    novo_username = message.text.split(" ", 1)[-1]

    # Verifica se o novo username é válido
    if is_valid_username(novo_username):
        # Atualiza o username na tabela de jogadores
        atualizar_username_jogador(user_id, novo_username)

        # Responde com uma mensagem de sucesso
        bot.send_message(chat_id, f"Username atualizado para: {novo_username}")
    else:
        # Responde com uma mensagem de erro se o username não for válido
        bot.send_message(
            chat_id,
            "Username inválido. Certifique-se de que tem entre 5 e 32 caracteres.",
        )


def processar_novo_usuario(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    novo_username = message.text.strip()

    # Verifique se o novo nome de usuário é válido
    if not util.is_username(novo_username):
        bot.send_message(chat_id, "Nome de usuário inválido. Tente novamente.")
        return

    # Verifique se o novo nome de usuário já está em uso
    if jogador_ja_cadastrado_pelo_username(novo_username):
        bot.send_message(chat_id, "Este nome de usuário já está em uso. Escolha outro.")
        return

    # Atualize o nome de usuário no banco de dados
    atualizar_username_jogador(user_id, novo_username)

    bot.send_message(
        chat_id, f"Seu nome de usuário foi atualizado para {novo_username}."
    )


def jogador_ja_cadastrado_pelo_username(username):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT COUNT(*) FROM jogadores WHERE username = '{username}'"
            )
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"Erro ao verificar se jogador já está cadastrado pelo username: {e}")
        finally:
            cursor.close()
            conexao.close()
    return False


def atualizar_username_jogador(user_id, novo_username):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"UPDATE jogadores SET username = '{novo_username}' WHERE userId = {user_id}"
            )
            conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar nome de usuário do jogador: {e}")
        finally:
            cursor.close()
            conexao.close()


@bot.message_handler(commands=["debug"])
def debug_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    jogador_info = obter_jogador_info(user_id)

    if jogador_info:
        bot.send_message(chat_id, f"Informações do jogador: {jogador_info}")
    else:
        bot.send_message(chat_id, "Jogador não encontrado.")


@bot.message_handler(commands=["my"])
def my_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Obtém informações do jogador
    jogador_info = obter_jogador_info(user_id)

    if jogador_info:
        # Obtém a quantidade total de cartas do jogador
        qtd_cartas_total = obter_qtd_cartas_jogador(user_id, "")

        # Menciona a mensagem original
        reply_to_message_id = message.message_id

        # Cria a mensagem a ser enviada
        mensagem_jogador = (
            "Jogador:\n"
            f"👤| Username: {jogador_info['username']}\n\n"
            "Informações:\n"
            f"🎰| Giros: {jogador_info['qtdGiros']}\n"
            f"🎴| Cartas: {qtd_cartas_total}"
        )

        # Envia as informações ao jogador
        bot.send_message(
            chat_id,
            mensagem_jogador,
            reply_to_message_id=reply_to_message_id,
        )
    else:
        bot.send_message(chat_id, "Jogador não encontrado.")


def obter_cartas_jogador(user_id):
    conexao = conectar_mysql()
    cartas_jogador = []

    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT cartaId, categoriaNome, obraNome, cartaNome, cartaImagem FROM cartas_jogadores WHERE jogadorId = {user_id} ORDER BY categoriaNome, obraNome"
            )
            cartas_jogador = cursor.fetchall()
        except Exception as e:
            print(f"Erro ao obter cartas do jogador do banco de dados: {e}")
        finally:
            cursor.close()
            conexao.close()

    print("Cartas do jogador:", cartas_jogador)
    return cartas_jogador


def obter_qtd_cartas_jogador(user_id, nome_da_carta):
    conexao = conectar_mysql()
    qtd_cartas = 0

    if conexao:
        try:
            cursor = conexao.cursor()
            if nome_da_carta:
                # Se o nome da carta for fornecido, conta apenas essa carta
                cursor.execute(
                    f"SELECT COUNT(*) FROM cartas_jogadores WHERE jogadorId = {user_id} AND cartaNome = '{nome_da_carta}'"
                )
            else:
                # Se nenhum nome de carta for fornecido, conta todas as cartas do jogador
                cursor.execute(
                    f"SELECT COUNT(*) FROM cartas_jogadores WHERE jogadorId = {user_id}"
                )

            qtd_cartas = cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao obter quantidade de cartas do jogador: {e}")
        finally:
            cursor.close()
            conexao.close()

    return qtd_cartas


def inserir_carta_jogador(
    jogador_id, username, categoria_nome, obra_nome, carta_nome, carta_imagem, carta_id
):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"INSERT INTO cartas_jogadores (jogadorId, username, categoriaNome, obraNome, cartaNome, cartaImagem, cartaId) "
                f"VALUES ({jogador_id}, '{username}', '{categoria_nome}', '{obra_nome}', '{carta_nome}', '{carta_imagem}', {carta_id})"
            )
            conexao.commit()

            # Retorna o ID da carta recém-inserida
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao inserir carta do jogador no banco de dados: {e}")
        finally:
            cursor.close()
            conexao.close()

    return None


def obter_jogador_info(user_id):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT userId, username, qtdGiros FROM jogadores WHERE userId = {user_id}"
            )
            jogador_info = cursor.fetchone()
            if jogador_info:
                return {
                    "userId": jogador_info[0],
                    "username": jogador_info[1],
                    "qtdGiros": jogador_info[2],
                }
        except Exception as e:
            print(f"Erro ao obter informações do jogador: {e}")
        finally:
            cursor.close()
            conexao.close()

    return None


def atualizar_qtd_giros_jogador(user_id, novo_saldo):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"UPDATE jogadores SET qtdGiros = {novo_saldo} WHERE userId = {user_id}"
            )
            conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar quantidade de giros do jogador: {e}")
        finally:
            cursor.close()
            conexao.close()


# Função para enviar mensagem de boas-vindas com informações sobre os comandos
def enviar_mensagem_boas_vindas(chat_id):
    mensagem = (
        "Bem-vindo(a) ao BearBot! Um bot de colecionar cartas gratuito e divertido.\n\n"
        "Aqui estão alguns comandos que você pode usar:\n\n"
        "/spin - para girar a roleta\n"
        "/colec - ver coleção\n"
        "/my - Ver suas informações\n"
        "/help - Ajuda"
    )
    bot.send_message(chat_id, mensagem)


@bot.message_handler(commands=["colec"])
def colec_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Defina o dicionário emojis_por_categoria aqui
    emojis_por_categoria = {
        "GamerBear": "🕹️",
        "DJBear": "🎧",
        "CineBear": "🍿",
        "OtakuBear": "🇯🇵",
        "LeitorBear": "📚",
        "LeitorBear": "🏀",
        # Adicione mais emojis e categorias conforme necessário
    }

    # Obtém as cartas do jogador
    cartas_jogador = obter_cartas_jogador(user_id)

    if cartas_jogador:
        # Cria um dicionário para organizar as cartas por categoria
        cartas_por_categoria = {}

        # Organiza as cartas no dicionário
        for carta in cartas_jogador:
            carta_id, categoria_nome, obra_nome, nome_da_carta, _ = carta

            # Se a categoria ainda não estiver no dicionário, adiciona
            if categoria_nome not in cartas_por_categoria:
                cartas_por_categoria[categoria_nome] = {
                    "cartas": set(),
                    "quantidade": {},
                }

            # Adiciona a carta ao conjunto da categoria
            cartas_por_categoria[categoria_nome]["cartas"].add(
                (nome_da_carta, obra_nome)
            )

        # Cria a mensagem a ser enviada
        mensagem_colecao = "Sua coleção de cartas:"

        for categoria, cartas_categoria in cartas_por_categoria.items():
            emoji_categoria = emojis_por_categoria.get(categoria, "❓")
            mensagem_colecao += f"\n\n{emoji_categoria} {categoria}\n----------------------------------------- \n"

            for carta_obra in cartas_categoria["cartas"]:
                nome, obra = carta_obra

                # Obtém a quantidade de cartas do jogador da mesma carta
                qtd_cartas = obter_qtd_cartas_jogador(user_id, nome)

                # Adiciona o emoji ✨ se houver mais de uma carta do mesmo tipo
                emoji_mais_cartas = " 🔂" if qtd_cartas > 1 else ""

                mensagem_colecao += f"{emoji_categoria} <b>{nome}</b> — <i>{obra}</i> {emoji_mais_cartas}\n"

        # Envia as cartas ao jogador
        bot.send_message(chat_id, mensagem_colecao, parse_mode="HTML")
    else:
        bot.send_message(chat_id, "Você não possui cartas ainda.")


@bot.message_handler(commands=["start"])
def start_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username

    # Adiciona o jogador ao dicionário (pode ser personalizado conforme necessário)
    jogador_info = inserir_jogador(user_id, username)

    # Envia a mensagem de boas-vindas
    enviar_mensagem_boas_vindas(chat_id)


def jogador_ja_cadastrado(user_id):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM jogadores WHERE userId = {user_id}")
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"Erro ao verificar se jogador já está cadastrado: {e}")
        finally:
            cursor.close()
            conexao.close()
    return False


def inserir_jogador(user_id, username):
    conexao = conectar_mysql()

    if conexao:
        try:
            # Verifica se o jogador já está cadastrado
            if jogador_ja_cadastrado(user_id):
                # Se o jogador já estiver cadastrado, retorna o ID existente
                return obter_jogador_info(user_id)

            # Se o jogador não estiver cadastrado, realiza a inserção
            with conexao.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO jogadores (userId, username, qtdCartas, qtdGiros) VALUES ('{user_id}','{username}', 0, 5)"
                )
                conexao.commit()

                # Retorna o ID do jogador recém-inserido
                return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao inserir jogador no banco de dados: {e}")
        finally:
            conexao.close()

    return None


# Função para obter as categorias cadastradas no banco de dados
def obter_categorias():
    conexao = conectar_mysql()
    categorias = []

    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute("SELECT DISTINCT categoriaNome FROM categorias;")
            categorias = [categoria[0] for categoria in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao obter categorias do banco de dados: {e}")
        finally:
            cursor.close()
            conexao.close()

    return categorias


def obter_obras(categoria):
    conexao = conectar_mysql()
    obras = []

    if conexao:
        try:
            cursor = conexao.cursor()

            # Adiciona aspas ao redor da categoria para tratar como string
            cursor.execute(
                f"SELECT obraNome FROM obras WHERE categoriaNome = %s ORDER BY RAND() LIMIT 6;",
                (categoria,),
            )
            obras = [obra[0] for obra in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao obter obras do banco de dados: {e}")
        finally:
            cursor.close()
            conexao.close()

    return obras


def obter_carta_por_id(carta_id):
    conexao = conectar_mysql()
    carta = None

    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM cartas WHERE cartaId = %s;", (carta_id,))
            print(f"Query executada: {cursor.statement}")
            print(f"Valor de carta_id: {carta_id}")
            carta = cursor.fetchone()
            print("Carta encontrada:", carta)
        except Exception as e:
            print(f"Erro ao obter carta por ID do banco de dados: {e}")
            import traceback

            traceback.print_exc()

        finally:
            cursor.close()
            conexao.close()

    return carta


def obter_carta_aleatoria(categoria_nome, obra_nome):
    conexao = conectar_mysql()
    carta = None

    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT cartaId, cartaNome, cartaImagem FROM cartas WHERE categoriaNome = %s AND obraNome = %s ORDER BY RAND() LIMIT 1;",
                (categoria_nome, obra_nome),
            )
            carta = cursor.fetchone()
        except Exception as e:
            print(f"Erro ao obter carta aleatória do banco de dados: {e}")
        finally:
            cursor.close()
            conexao.close()

    return carta


def obter_carta_info(nome_da_carta):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                f"SELECT cartaId FROM cartas WHERE cartaNome = '{nome_da_carta}' LIMIT 1"
            )
            carta_info = cursor.fetchone()
            return carta_info
        except Exception as e:
            print(f"Erro ao obter informações da carta: {e}")
        finally:
            cursor.close()
            conexao.close()

    return None


def processar_roleta(chat_id, username, categoria_escolhida, obra_escolhida):
    print(
        f"Girando roleta para o chat ID {chat_id} na categoria {categoria_escolhida} e obra {obra_escolhida}"
    )

    jogador_info = obter_jogador_info(chat_id)

    if jogador_info and jogador_info["qtdGiros"] > 0:
        conexao = conectar_mysql()
        if conexao:
            try:
                carta_aleatoria = obter_carta_aleatoria(
                    categoria_escolhida, obra_escolhida
                )

                if carta_aleatoria:
                    carta_id = carta_aleatoria["cartaId"]
                    nome_da_carta = carta_aleatoria["cartaNome"]
                    link_imagem = carta_aleatoria["cartaImagem"]
                    emojis_por_categoria = {
                        "GamerBear": "🕹️",
                        "DJBear": "🎧",
                        "CineBear": "🍿",
                        "OtakuBear": "🇯🇵",
                        "LeitorBear": "📚",
                        "EsporteBear": "🏀",
                    }

                    # Inserir a carta do jogador no banco de dados
                    carta_id_jogador = inserir_carta_jogador(
                        jogador_info["userId"],
                        username,
                        categoria_escolhida,
                        obra_escolhida,
                        nome_da_carta,
                        link_imagem,
                        carta_id,
                    )

                    # Atualiza a quantidade de tiradas da carta no banco de dados
                    atualizar_qtd_tiradas_carta(carta_id)

                    # Obtém a quantidade de cartas do jogador da mesma carta
                    qtd_cartas = obter_qtd_cartas_jogador(
                        jogador_info["userId"], nome_da_carta
                    )

                    carta_info = obter_carta_por_id(carta_id)

                    # Adiciona o emoji da categoria ao nome da categoria
                    emoji_categoria = emojis_por_categoria.get(categoria_escolhida, "❓")

                    # Inclui o ID da carta na mensagem
                    mensagem = (
                        f"{emoji_categoria} <code>{carta_id}</code>. <b>{nome_da_carta}</b> \n"
                        f"<i>{obra_escolhida}</i>\n\n"
                        f"{jogador_info['username']} ({qtd_cartas}x)"
                    )

                    # Apaga a mensagem original com os botões
                    bot.delete_message(
                        chat_id, jogadores_registrados[chat_id]["message_id"]
                    )

                    # Envia a carta com imagem e informações
                    bot.send_photo(
                        chat_id, link_imagem, caption=mensagem, parse_mode="HTML"
                    )

                    # Atualiza a quantidade de cartas do jogador e os giros restantes
                    atualizar_qtd_cartas_jogador(jogador_info["userId"])
                    novo_saldo_giros = jogador_info["qtdGiros"] - 1
                    atualizar_qtd_giros_jogador(
                        jogador_info["userId"], novo_saldo_giros
                    )

                else:
                    mensagem = "Não foi possível obter uma carta. Tente novamente."
                    bot.send_message(chat_id, mensagem)
            except Exception as e:
                print(f"Erro ao girar a roleta: {e}")
            finally:
                if conexao.is_connected():
                    conexao.close()
                    print("Conexão ao MySQL fechada.")
    else:
        bot.send_message(chat_id, "Você não tem giros suficientes para girar a roleta.")


def atualizar_qtd_cartas_jogador(jogador_id):
    conexao = conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(
                f"UPDATE jogadores SET qtdCartas = qtdCartas + 1 WHERE userId = {jogador_id}"
            )
            conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar quantidade de cartas do jogador: {e}")
        finally:
            cursor.close()
            conexao.close()


# Comando /spin para iniciar o processo de roleta
@bot.message_handler(commands=["spin"])
def spin_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username  # Adicione esta linha para obter o username

    jogador_info = obter_jogador_info(chat_id)

    if jogador_info and jogador_info["qtdGiros"] > 0:
        categorias = obter_categorias()
        emojis_por_categoria = {
            "GamerBear": "🕹️",
            "DJBear": "🎧",
            "CineBear": "🍿",
            "OtakuBear": "🇯🇵",
            "LeitorBear": "📚",
            "EsporteBear": "🏀",
        }

        markup = types.InlineKeyboardMarkup(row_width=2)
        for i, categoria in enumerate(categorias, start=1):
            emoji_categoria = emojis_por_categoria.get(categoria, "❓")

            categoria_button = types.InlineKeyboardButton(
                f"{i}. {categoria.capitalize()} - {emoji_categoria}",
                callback_data=f"command_{categoria}",
            )
            markup.add(categoria_button)

        message_to_delete = bot.send_message(
            chat_id,
            "Escolha uma categoria:",
            reply_markup=markup,
        ).message_id

        jogadores_registrados[chat_id] = {
            "categoria": None,
            "obra": None,
            "message_id": message_to_delete,
            "username": username,  # Adicione o username ao dicionário do jogador
        }
    else:
        bot.send_message(chat_id, "Você não tem giros suficientes para girar a roleta.")


@bot.callback_query_handler(func=lambda call: True)
def answer(callback):
    if callback.message:
        chat_id = callback.message.chat.id

        # Verifica se o callback é para uma obra específica
        if callback.data.startswith("command_obra_"):
            obra_nome = callback.data[len("command_obra_") :]

            # Garante que a chave "obra" exista no dicionário
            if chat_id not in jogadores_registrados:
                jogadores_registrados[chat_id] = {}

            # Atualiza a obra escolhida no dicionário
            jogadores_registrados[chat_id]["obra"] = obra_nome

            # Obtém a categoria escolhida
            categoria_escolhida = jogadores_registrados[chat_id]["categoria"]

            # Mensagem de depuração
            print(f"Categoria: {categoria_escolhida}, Obra: {obra_nome}")

            # Inicia imediatamente o processo de roleta, sem verificar giros
            processar_roleta(
                chat_id,
                jogadores_registrados[chat_id]["username"],
                categoria_escolhida,
                obra_nome,
            )

        elif callback.data.startswith("command_") and jogadores_registrados.get(
            chat_id
        ):
            # Se não for uma obra específica e o jogador está registrado, trata como escolha de categoria
            categoria_escolhida = callback.data[len("command_") :]

            # Atualiza a categoria escolhida no dicionário
            jogadores_registrados[chat_id]["categoria"] = categoria_escolhida

            # Obtém as obras para a categoria escolhida
            obras = obter_obras(categoria_escolhida)

            # Cria os botões para as obras
            markup = types.InlineKeyboardMarkup(row_width=2)
            for obra in obras:
                obra_button = types.InlineKeyboardButton(
                    f"{obra}",
                    callback_data=f"command_obra_{obra}",
                )
                markup.add(obra_button)

            # Edita a mensagem original para mostrar as obras
            bot.edit_message_text(
                "Escolha uma obra:",
                chat_id=chat_id,
                message_id=jogadores_registrados[chat_id]["message_id"],
                reply_markup=markup,
            )

        else:
            bot.send_message(chat_id, "Comando inválido.")


# Inicie o bot
bot.polling()
