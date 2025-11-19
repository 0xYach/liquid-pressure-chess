import chess
from stockfish import Stockfish
import random
import time
import math
from datetime import datetime, timedelta

# --- Initialize Stockfish ---
ENGINE_PATH = "/data/data/com.termux/files/home/stockfish/stockfish-android-armv8"
sf = Stockfish(ENGINE_PATH)
sf.set_skill_level(20)

# --- Ask player color ---
color = input("Are you playing as White or Black? (w/b): ").strip().lower()
player_is_white = color == "w"

# --- Initialize python-chess board ---
board = chess.Board()

# --- Game Clock Setup ---
GAME_DURATION = 10 * 60  # 10 minutes in seconds
engine_time_remaining = GAME_DURATION
opponent_time_remaining = GAME_DURATION
last_move_time = datetime.now()

# --- Liquid Pressure Style Parameters ---
LIQUID_STYLE = {
    "pressure": 0.0,
    "flow_momentum": 0.0,
    "time_awareness": "balanced",  # balanced/aggressive/conservative
    "phase": "calm_flow"  # calm_flow/building_waves/crushing_tide
}

# --- Time Management Functions ---
def update_clock(is_engine_move=True):
    """Update time remaining for the appropriate player"""
    global last_move_time, engine_time_remaining, opponent_time_remaining
    
    current_time = datetime.now()
    elapsed = (current_time - last_move_time).total_seconds()
    last_move_time = current_time
    
    if is_engine_move:
        opponent_time_remaining -= elapsed
    else:
        engine_time_remaining -= elapsed
    
    return elapsed

def get_time_pressure(time_remaining, move_number):
    """Calculate time pressure factor (0-1, higher = more pressure)"""
    expected_moves = 40  # Typical game length
    time_per_move = GAME_DURATION / expected_moves
    moves_remaining = expected_moves - move_number
    
    if moves_remaining <= 0:
        return 1.0
    
    available_time = time_remaining / moves_remaining
    pressure = max(0, 1.0 - (available_time / time_per_move))
    return min(1.0, pressure)

def adaptive_thinking_time(board, time_remaining, pressure):
    """Adjust thinking time based on game situation and time remaining"""
    move_number = board.fullmove_number
    time_pressure = get_time_pressure(time_remaining, move_number)
    
    # Base thinking time from liquid style
    if pressure < 0.3:
        base_time = random.uniform(2.0, 4.0)  # Calm flow
    elif pressure < 0.7:
        base_time = random.uniform(3.0, 6.0)  # Building waves  
    else:
        base_time = random.uniform(1.5, 3.5)  # Crushing tide
    
    # Reduce thinking time under time pressure
    if time_pressure > 0.5:
        base_time *= (1.0 - time_pressure * 0.6)
    
    # Quick moves in time trouble
    if time_remaining < 60:  # Less than 1 minute
        base_time = random.uniform(0.5, 2.0)
    elif time_remaining < 180:  # Less than 3 minutes
        base_time = random.uniform(1.0, 3.0)
    
    # Ensure minimum thinking time
    base_time = max(0.3, base_time)
    
    # Don't use more than 10% of remaining time
    max_reasonable = time_remaining * 0.1
    base_time = min(base_time, max_reasonable)
    
    return base_time

def display_time_remaining():
    """Show current time situation"""
    engine_min = int(engine_time_remaining // 60)
    engine_sec = int(engine_time_remaining % 60)
    opp_min = int(opponent_time_remaining // 60)
    opp_sec = int(opponent_time_remaining % 60)
    
    print(f"⏰ Your time: {engine_min:02d}:{engine_sec:02d} | Opponent: {opp_min:02d}:{opp_sec:02d}")

# --- Liquid Pressure Core Logic ---
def update_liquid_momentum(board, move_uci, time_used):
    """Update liquid style parameters"""
    # Momentum builds with effective moves
    LIQUID_STYLE["flow_momentum"] = min(1.0, LIQUID_STYLE["flow_momentum"] + 0.06)
    
    # Pressure adjusts based on position and time
    position_complexity = len(list(board.legal_moves)) / 20.0
    time_efficiency = min(1.0, time_used / 5.0)  # Normalize time usage
    
    LIQUID_STYLE["pressure"] = (LIQUID_STYLE["flow_momentum"] * 0.6 + 
                               position_complexity * 0.3 + 
                               time_efficiency * 0.1)
    
    # Update phase based on pressure
    if LIQUID_STYLE["pressure"] < 0.4:
        LIQUID_STYLE["phase"] = "calm_flow"
    elif LIQUID_STYLE["pressure"] < 0.8:
        LIQUID_STYLE["phase"] = "building_waves"
    else:
        LIQUID_STYLE["phase"] = "crushing_tide"

def get_positional_tension(board):
    """Calculate how tense/complex the position is"""
    tension = 0.0
    
    # More pieces = more complexity
    piece_count = len(board.piece_map())
    tension += (piece_count / 32.0) * 0.3
    
    # Checks and captures increase tension
    if board.is_check():
        tension += 0.2
    if any(board.is_capture(move) for move in board.legal_moves):
        tension += 0.2
    
    # Many legal moves = complex position
    move_count = len(list(board.legal_moves))
    tension += min(0.3, move_count / 50.0)
    
    return min(1.0, tension)

# --- Liquid Style Move Selection ---
def liquid_style_move_selection(board, sf, time_remaining):
    """Liquid-style move selection with time awareness"""
    pressure = LIQUID_STYLE["pressure"]
    time_pressure = get_time_pressure(time_remaining, board.fullmove_number)
    position_tension = get_positional_tension(board)
    
    # Adjust skill level based on situation
    if time_pressure > 0.7:
        skill = random.randint(16, 18)  # Slightly lower in time trouble
    else:
        skill = random.randint(18, 20)
    sf.set_skill_level(skill)
    
    # Choose number of moves to consider based on time
    if time_pressure > 0.8:
        top_n = 3  # Quick decisions under pressure
    elif position_tension > 0.7:
        top_n = 6  # More analysis in complex positions
    else:
        top_n = 4  # Balanced approach
    
    top_moves = sf.get_top_moves(top_n)
    if not top_moves:
        return None
    
    # Time-aware move selection
    if time_remaining < 30:  # Blitz mode under 30 seconds
        return blitz_mode_moves(top_moves)
    elif LIQUID_STYLE["phase"] == "calm_flow":
        return calm_flow_moves(board, top_moves, time_pressure)
    elif LIQUID_STYLE["phase"] == "building_waves":
        return building_waves_moves(board, top_moves, time_pressure)
    else:  # crushing_tide
        return crushing_tide_moves(board, top_moves, time_pressure)

def blitz_mode_moves(top_moves):
    """Quick decisions in time trouble"""
    # 80% best move, 20% second best
    if random.random() < 0.8:
        return top_moves[0]['Move']
    else:
        return top_moves[1]['Move'] if len(top_moves) > 1 else top_moves[0]['Move']

def calm_flow_moves(board, top_moves, time_pressure):
    """Calm, positional building phase"""
    # Prefer solid, developing moves
    solid_moves = []
    for move_info in top_moves:
        move = move_info['Move']
        if is_calm_move(board, move):
            solid_moves.append(move_info)
    
    if solid_moves and random.random() < 0.7:
        chosen = random.choice(solid_moves[:3])
    else:
        # Natural flow with imperfection
        if random.random() < max(0.2, time_pressure * 0.3):
            chosen = random.choice(top_moves[1:4]) if len(top_moves) > 3 else top_moves[0]
        else:
            chosen = top_moves[0]
    
    return chosen['Move']

def is_calm_move(board, move_uci):
    """Check if move maintains calm positional flow"""
    move = chess.Move.from_uci(move_uci)
    # Avoid early aggression unless clearly best
    if board.is_check() or board.is_capture(move):
        return False
    # Prefer developing and centralizing moves
    piece = board.piece_at(move.from_square)
    return piece and piece.piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP]

def building_waves_moves(board, top_moves, time_pressure):
    """Building pressure phase"""
    # Weight moves by pressure-building potential
    weighted_moves = []
    for i, move_info in enumerate(top_moves):
        weight = calculate_pressure_weight(board, move_info['Move'], i)
        # Reduce weight slightly under time pressure
        weight *= (1.0 - time_pressure * 0.2)
        weighted_moves.append((move_info, weight))
    
    moves, weights = zip(*weighted_moves)
    chosen_info = random.choices(moves, weights=weights, k=1)[0]
    return chosen_info['Move']

def crushing_tide_moves(board, top_moves, time_pressure):
    """Overwhelming pressure phase"""
    # Maximum strength with decisive intent
    if random.random() < 0.8 - (time_pressure * 0.3):
        return top_moves[0]['Move']  # Crushing force
    else:
        # Maintain pressure while avoiding perfection
        return random.choice(top_moves[1:3])['Move'] if len(top_moves) > 2 else top_moves[0]['Move']

def calculate_pressure_weight(board, move_uci, rank):
    """Calculate pressure-building weight for move"""
    base_weight = 1.0 / (rank + 1)
    move = chess.Move.from_uci(move_uci)
    
    # Pressure-building factors
    if board.is_check():
        base_weight *= 1.3
    if board.is_capture(move):
        base_weight *= 1.2
    if attacks_important_square(board, move):
        base_weight *= 1.25
    
    return base_weight

def attacks_important_square(board, move):
    """Check if move attacks important squares"""
    target = move.to_square
    # Center control
    if target in [chess.E4, chess.E5, chess.D4, chess.D5]:
        return True
    # King attack potential
    opponent_king = board.king(not board.turn)
    if opponent_king and chess.square_distance(target, opponent_king) <= 2:
        return True
    return False

# --- Board display ---
def print_board(board, player_is_white=True):
    ranks = []
    for rank in range(8, 0, -1):
        row = []
        for file in range(1, 9):
            square = chess.square(file - 1, rank - 1)
            piece = board.piece_at(square)
            row.append(piece.symbol() if piece else ".")
        ranks.append(row)
    if not player_is_white:
        ranks = [list(reversed(r)) for r in ranks]
    unicode_pieces = {"K":"♔","Q":"♕","R":"♖","B":"♗","N":"♘","P":"♙",
                      "k":"♚","q":"♛","r":"♜","b":"♝","n":"♞","p":"♟"}
    for r in ranks:
        print(" ".join(unicode_pieces.get(p, p) for p in r))
    print()

# --- Helper to sync Stockfish and python-chess ---
def make_move(move_uci):
    board.push_uci(move_uci)
    sf.make_moves_from_current_position([move_uci])

# --- Main game loop ---
print(f"🌊 Liquid Pressure Style Engaged - 10:00 Game Clock")
print(f"💧 Phase: {LIQUID_STYLE['phase'].replace('_', ' ').title()}")
print(f"⏰ Time management: Balanced approach\n")

if player_is_white:
    print("You are White. Liquid Pressure begins the flow...\n")
    while not board.is_game_over() and engine_time_remaining > 0 and opponent_time_remaining > 0:
        print("\n" + "="*50)
        display_time_remaining()
        print(f"💧 Pressure: {LIQUID_STYLE['pressure']:.1%} | Phase: {LIQUID_STYLE['phase'].replace('_', ' ').title()}")
        print_board(board, player_is_white)

        # Liquid Pressure move
        best_move = liquid_style_move_selection(board, sf, engine_time_remaining)
        if best_move:
            thinking_time = adaptive_thinking_time(board, engine_time_remaining, LIQUID_STYLE['pressure'])
            
            print(f"💭 Liquid Pressure thinking for {thinking_time:.1f}s...")
            time.sleep(thinking_time)
            
            update_clock(is_engine_move=True)
            make_move(best_move)
            update_liquid_momentum(board, best_move, thinking_time)
            print(f"💧 Liquid Pressure flows: {best_move}")
        else:
            print("♟️ No legal moves left.")
            break

        if board.is_game_over() or engine_time_remaining <= 0:
            break

        # Opponent move
        while True:
            opp_move = input("Opponent move (UCI) or 'quit': ").strip()
            if opp_move.lower() == "quit":
                exit("Game exited.")
            
            try:
                move_obj = chess.Move.from_uci(opp_move)
                if move_obj in board.legal_moves:
                    update_clock(is_engine_move=False)
                    make_move(opp_move)
                    update_liquid_momentum(board, opp_move, 0)  # Opponent's time affects flow
                    break
                else:
                    print("❌ Illegal move. Try again.")
            except ValueError:
                print("❌ Invalid format. Use UCI (e.g., e2e4)")

else:
    print("You are Black. Liquid Pressure awaits the flow...\n")
    while not board.is_game_over() and engine_time_remaining > 0 and opponent_time_remaining > 0:
        print("\n" + "="*50)
        display_time_remaining()
        print(f"💧 Pressure: {LIQUID_STYLE['pressure']:.1%} | Phase: {LIQUID_STYLE['phase'].replace('_', ' ').title()}")
        print_board(board, player_is_white)

        # Opponent move first
        while True:
            opp_move = input("Opponent move (UCI) or 'quit': ").strip()
            if opp_move.lower() == "quit":
                exit("Game exited.")
            
            try:
                move_obj = chess.Move.from_uci(opp_move)
                if move_obj in board.legal_moves:
                    update_clock(is_engine_move=False)
                    make_move(opp_move)
                    update_liquid_momentum(board, opp_move, 0)
                    break
                else:
                    print("❌ Illegal move. Try again.")
            except ValueError:
                print("❌ Invalid format. Use UCI (e.g., e2e4)")

        if board.is_game_over() or opponent_time_remaining <= 0:
            break

        # Liquid Pressure response
        best_move = liquid_style_move_selection(board, sf, engine_time_remaining)
        if best_move:
            thinking_time = adaptive_thinking_time(board, engine_time_remaining, LIQUID_STYLE['pressure'])
            
            print(f"💭 Liquid Pressure thinking for {thinking_time:.1f}s...")
            time.sleep(thinking_time)
            
            update_clock(is_engine_move=True)
            make_move(best_move)
            update_liquid_momentum(board, best_move, thinking_time)
            print(f"💧 Liquid Pressure flows: {best_move}")
        else:
            print("♟️ No legal moves left.")
            break

# --- Game over ---
print("\n" + "="*50)
print("GAME OVER!")
display_time_remaining()

if engine_time_remaining <= 0:
    print("⏰ Liquid Pressure ran out of time!")
elif opponent_time_remaining <= 0:
    print("⏰ Opponent ran out of time! Liquid Pressure wins!")
elif board.is_checkmate():
    if LIQUID_STYLE['pressure'] > 0.7:
        print("🌊 CRUSHING TIDE! Liquid Pressure overwhelms completely!")
    else:
        print("💧 Flowing checkmate! Water finds its path.")
elif board.is_stalemate():
    print("💧 Still waters - stalemate.")
elif board.is_insufficient_material():
    print("💧 Evaporated to draw - insufficient material.")
elif board.is_fifty_moves():
    print("💧 Flow stagnated - fifty move rule.")
else:
    print("💧 Game ended.")

print(f"\nFinal Pressure: {LIQUID_STYLE['pressure']:.1%}")
