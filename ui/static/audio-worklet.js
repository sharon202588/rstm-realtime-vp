class Pcm16Downsampler extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetRate = 16000;
    this.pending = [];
    this.phase = 0;
  }

  process(inputs) {
    const input = inputs[0] && inputs[0][0];
    if (!input || input.length === 0) return true;

    const ratio = sampleRate / this.targetRate;
    const output = [];
    let index = this.phase;
    while (index < input.length) {
      const left = Math.floor(index);
      const right = Math.min(left + 1, input.length - 1);
      const fraction = index - left;
      output.push(input[left] + (input[right] - input[left]) * fraction);
      index += ratio;
    }
    this.phase = index - input.length;

    const pcm = new Int16Array(output.length);
    let peak = 0;
    for (let i = 0; i < output.length; i += 1) {
      const sample = Math.max(-1, Math.min(1, output[i]));
      peak = Math.max(peak, Math.abs(sample));
      pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    this.port.postMessage({ pcm: pcm.buffer, peak }, [pcm.buffer]);
    return true;
  }
}

registerProcessor("pcm16-downsampler", Pcm16Downsampler);
