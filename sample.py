"""
Sample from a trained model
"""
import os
import pickle
from contextlib import nullcontext
import torch
import tiktoken
from model import GPTConfig, GPT
import chess
import chess.pgn

# -----------------------------------------------------------------------------
init_from = 'resume' # either 'resume' (from an out_dir) or a gpt2 variant (e.g. 'gpt2-xl')
out_dir = 'out' # ignored if init_from is not 'resume'
start = "\n" # or "<|endoftext|>" or etc. Can also specify a file, use as: "FILE:prompt.txt"
num_samples = 1 # number of samples to draw
max_new_tokens = 500 # number of tokens generated in each sample
temperature = 0.8 # 1.0 = no change, < 1.0 = less random, > 1.0 = more random, in predictions
top_k = 200 # retain only the top_k most likely tokens, clamp others to have 0 probability
seed = 1337
device = 'cuda' # examples: 'cpu', 'cuda', 'cuda:0', 'cuda:1', etc.
dtype = 'bfloat16' if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else 'float16' # 'float32' or 'bfloat16' or 'float16'
compile = False # use PyTorch 2.0 to compile the model to be faster
exec(open('configurator.py').read()) # overrides from command line or config file
# -----------------------------------------------------------------------------

torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cuda.matmul.allow_tf32 = True # allow tf32 on matmul
torch.backends.cudnn.allow_tf32 = True # allow tf32 on cudnn
device_type = 'cuda' if 'cuda' in device else 'cpu' # for later use in torch.autocast
ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = nullcontext() if device_type == 'cpu' else torch.amp.autocast(device_type=device_type, dtype=ptdtype)

# model
if init_from == 'resume':
    # init from a model saved in a specific directory
    ckpt_path = os.path.join(out_dir, 'ckpt.pt')
    checkpoint = torch.load(ckpt_path, map_location=device)
    gptconf = GPTConfig(**checkpoint['model_args'])
    model = GPT(gptconf)
    state_dict = checkpoint['model']
    unwanted_prefix = '_orig_mod.'
    for k,v in list(state_dict.items()):
        if k.startswith(unwanted_prefix):
            state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
    model.load_state_dict(state_dict)
elif init_from.startswith('gpt2'):
    # init from a given GPT-2 model
    model = GPT.from_pretrained(init_from, dict(dropout=0.0))

model.eval()
model.to(device)
if compile:
    model = torch.compile(model) # requires PyTorch 2.0 (optional)

# look for the meta pickle in case it is available in the dataset folder
load_meta = False
if init_from == 'resume' and 'config' in checkpoint and 'dataset' in checkpoint['config']: # older checkpoints might not have these...
    meta_path = os.path.join('data', checkpoint['config']['dataset'], 'meta.pkl')
    load_meta = os.path.exists(meta_path)
if load_meta:
    print(f"Loading meta from {meta_path}...")
    with open(meta_path, 'rb') as f:
        meta = pickle.load(f)
    # TODO want to make this more general to arbitrary encoder/decoder schemes
    stoi, itos = meta['stoi'], meta['itos']
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda l: [itos[i] for i in l]
else:
    # ok let's assume gpt-2 encodings by default
    print("No meta.pkl found, assuming GPT-2 encodings...")
    enc = tiktoken.get_encoding("gpt2")
    encode = lambda s: enc.encode(s, allowed_special={"<|endoftext|>"})
    decode = lambda l: enc.decode(l)


#Jos ei tarvitse tarkistaa annetun siirron laillisuutta:

def validate_move(moves: list):
    game = chess.pgn.Game()
    board = chess.Board()
    game.headers["Event"] = "Example"
    for move in moves[:-1]:
        uci = board.push_san(move).uci()
        mv = chess.Move.from_uci(uci)
        game.end().add_main_variation(mv)
    try:
        legal_moves = list(board.legal_moves)
        uci = board.push_san(moves[-1]).uci()
        mv = chess.Move.from_uci(uci)
        if mv in legal_moves:
            game.end().add_main_variation(mv)
            return True
    except:
        return False

def generate_move(moves: list):
    while True:
        x = (torch.tensor(moves, dtype=torch.long, device=device)[None, ...])
        y = model.generate(x, max_new_tokens, temperature=temperature, top_k=top_k)
        generated_token = y[0][len(moves)].item()
        generated_move = itos[generated_token]
        check = validate_moves(moves + [generated_move])
        if check:
            moves.append(generated_move)
            return moves

# ------------------------------------------

def validate_moves(moves: list):
    game = chess.pgn.Game()
    board = chess.Board()
    game.headers["Event"] = "Example"
    for move in moves[:-1]:
        uci = board.push_san(move).uci()
        mv = chess.Move.from_uci(uci)
        game.end().add_main_variation(mv)
    try:
        legal_moves = list(board.legal_moves)
        uci = board.push_san(moves[-1]).uci()
        mv = chess.Move.from_uci(uci)
        if mv in legal_moves:
            game.end().add_main_variation(mv)
            return "legal move"
    except chess.IllegalMoveError:
        return "move not allowed"
    except chess.AmbiguousMoveError:
        return "move not allowed"

def generate_game(moves: list):
    last_move = moves[-1]
    if last_move not in stoi.keys():
        print("Invalid move, try again")
        pass
    move_id = stoi[last_move]
    check = validate_moves(moves)
    if check == "move not allowed":
        print("Move not allowed, try again")
        pass
    elif check == "legal move":
        while True:
            x = (torch.tensor(moves, dtype=torch.long, device=device)[None, ...])
            y = model.generate(x, max_new_tokens, temperature=temperature, top_k=top_k)
            generated_token = y[0][len(moves)].item()
            check = validate_moves(moves + [itos[generated_token]])
            if check == "legal move":
                moves.append(itos[generated_token])
                return moves


"""
game = chess.pgn.Game()
board = chess.Board()
game.headers["Event"] = "Example"

def add_move_to_game(gamemove, status):
    if gamemove == "\n":
        return "game over"
    try:
        legal_moves = list(board.legal_moves)
        uci = board.push_san(gamemove).uci()
        mv = chess.Move.from_uci(uci)
        if mv in legal_moves:
            game.end().add_main_variation(mv)
            return "legal move"
    except chess.IllegalMoveError:
        return "move not allowed"
    except chess.AmbiguousMoveError:
        return "move not allowed"


all_ids = []

while True:
    with torch.no_grad():
        with ctx:
                # Haetaan uusi siirto käyttäjältä
                start = input("Next move: ")
                if start == "":
                    break
                elif exit_game:
                    break
                start_moves = start.strip().split(", ")
                for start in start_moves:
                    if start not in stoi.keys():
                        print("Invalid move, try again")
                        break
                    start_id = stoi[start]
                    check = add_move_to_game(start, "given")
                    if check == "move not allowed":
                        print("Move not allowed, try again")
                        break
                    elif check == "game over":
                        exit_game = True
                        break
                    elif check == "legal move":
                        all_ids.append(start_id)
                        x = (torch.tensor(all_ids, dtype=torch.long, device=device)[None, ...])
                        while True:
                            y = model.generate(x, max_new_tokens, temperature=temperature, top_k=top_k)
                            generated_token = y[0][len(all_ids)].item()
                            check = add_move_to_game(itos[generated_token], "generated")
                            if check == "legal move":
                                all_ids.append(generated_token)
                                # Tässä lähetetään pelin siirrot eli all_ids? Dekoodataan ensin
                                # all_moves = decode(all_ids)
                                break
"""