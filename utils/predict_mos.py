import io
import numpy as np
import torch
import torch.nn as nn
import torchaudio
import numpy as np
import soundfile as sf
from pathlib import Path
from demucs import pretrained
from demucs.apply import apply_model
from transformers import AutoFeatureExtractor, AutoModel

torchaudio.set_audio_backend("soundfile")

class RegressorMLP(nn.Module):
    def __init__(self, in_dim, hidden_dim=512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(hidden_dim, hidden_dim//2),
            nn.ReLU(),
            nn.Dropout(0.1),

            nn.Linear(hidden_dim//2, 1)
        )

    def forward(self, x):
        x = self.net(x).squeeze(-1)
        return x
    


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SAMPLE_RATE = 16000
EMBED_LAYER_POOLING = "mean"

WAVLM_MODEL = "microsoft/wavlm-large"
extractor = AutoFeatureExtractor.from_pretrained(WAVLM_MODEL)
wavlm = AutoModel.from_pretrained(WAVLM_MODEL).to(DEVICE)
wavlm.eval()

MLP_PATH = Path(__file__).parent.parent / "models" / "mos-predictor" / "wavlm_mlp_mos_regressor.pt"
wavlm_mlp = RegressorMLP(in_dim=1024, hidden_dim=512).to(DEVICE)
state_dict = torch.load(MLP_PATH, map_location=DEVICE)
wavlm_mlp.load_state_dict(state_dict)
wavlm_mlp.eval()

demucs_model = pretrained.get_model("htdemucs").to(DEVICE)
demucs_model.eval()

def load_wav_bytes(wav_bytes, target_sr=16000):
    buffer = io.BytesIO(wav_bytes)
    waveform, sr = torchaudio.load(buffer)
    
    if waveform.ndim == 1:
        waveform = waveform.unsqueeze(0)

    if sr != target_sr:
        waveform = torchaudio.transforms.Resample(sr, target_sr)(waveform)
        sr = target_sr

    return waveform, sr

def predict_mos_from_wav_file(wav_path):

    with open(wav_path, "rb") as f:
        wav_bytes = f.read()

    emb = vocal_wavlm_embedding(wav_bytes)

    emb_tensor = torch.tensor(emb, dtype=torch.float32).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        mos_pred = wavlm_mlp(emb_tensor).cpu().item()

    return mos_pred


def batch_predict_mos(file_list, base_dir=None):
    """
    file_list: list of filenames
    base_dir: optional folder prefix
    Returns: dict {filename: predicted MOS}
    """
    results = {}
    for f in file_list:
        full_path = Path(f) if base_dir is None else Path(base_dir) / f
        results[str(f)] = predict_mos_from_wav_file(full_path)
    return results


def demucs_extract_vocals(wav_bytes, model_name="htdemucs"):
    #buffer = io.BytesIO(wav_bytes)
    #waveform, sr = torchaudio.load(buffer)
    # htdemucs is trained on 44.1 kHz audio; separate at its rate, resample to 16 kHz afterwards
    waveform, sr = load_wav_bytes(wav_bytes, target_sr=demucs_model.samplerate)

    if waveform.shape[0] == 1:
        waveform = waveform.repeat(2, 1)

    waveform = waveform.unsqueeze(0)

    #model = pretrained.get_model(model_name).to(DEVICE)
    #model.eval()

    with torch.no_grad():
        separated = apply_model(demucs_model, waveform.to(DEVICE), split=True, device=DEVICE)[0]

    vocals_idx = demucs_model.sources.index("vocals")
    vocals = separated[vocals_idx].cpu()  # (C, T)

    return vocals, sr



def extract_embedding_from_wave(wave: np.ndarray, sr: int = SAMPLE_RATE):
    """
    wave: 1D numpy float32 array
    """
    inputs = extractor(
        wave,
        sampling_rate=sr,
        return_tensors="pt",
        padding=True
    ).to(DEVICE)

    with torch.no_grad():
        out = wavlm(**inputs)
        last_hidden = out.last_hidden_state.squeeze(0).cpu().numpy()

    if EMBED_LAYER_POOLING == "mean":
        return last_hidden.mean(axis=0)
    elif EMBED_LAYER_POOLING == "max":
        return last_hidden.max(axis=0)
    else:
        return last_hidden[0]
    


def vocal_wavlm_embedding(wav_bytes):
    vocals, sr = demucs_extract_vocals(wav_bytes)

    # Convert to mono
    vocals = vocals.mean(dim=0).numpy().astype(np.float32)

    # Resample to 16kHz
    if sr != SAMPLE_RATE:
        vocals = torchaudio.transforms.Resample(sr, SAMPLE_RATE)(torch.tensor(vocals)).numpy()

    return extract_embedding_from_wave(vocals, SAMPLE_RATE)