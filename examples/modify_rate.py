import soundfile as sf
import librosa

###
# 单声道 改变采样率
###
# audio, sr = librosa.load('twinkle_twinkle_mono.wav')

# target_sr = 16000  # 目标采样率
# resampled_audio = librosa.resample(audio, sr, target_sr)

# sf.write('twinkle_twinkle_mono_16k.wav',
#          resampled_audio, target_sr, subtype='PCM_16')


###
# 立体声 改变采样率，发现librosa自动转换成了单声道
###

audio, sr = librosa.load('twinkle_twinkle.wav')

target_sr = 16000  # 目标采样率
resampled_audio = librosa.resample(audio, sr, target_sr)

sf.write('twinkle_twinkle_16k.wav',
         resampled_audio, target_sr, subtype='PCM_16')
