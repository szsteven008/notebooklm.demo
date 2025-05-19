import argparse
from docling.document_converter import DocumentConverter
from openai import OpenAI
import re
from kokoro import KPipeline
import sounddevice as sd
import soundfile as sf
import scipy.io.wavfile as wav

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the main application.")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to the input file.",
    )
    parser.add_argument(
        "-o", 
        "--output",
        type=str,
        required=True,
        help="Path to the output file.",
    )
    parser.add_argument(
        "-b", 
        "--base-url",
        type=str,
        default="http://localhost:8080/v1",
        help="base url.",
    )
    args = parser.parse_args()

    converter = DocumentConverter()
    doc = converter.convert(args.input).document
    prompt = doc.export_to_text() + "\nno_think"

    print("pdf parse done!")

    client = OpenAI(
        api_key="sk-xxx",
        base_url=args.base_url,
    )

    system_prompt = '''
        你是一个专业的播客编剧，请根据以下PDF文档的内容创作一段适合播客播放的对话剧本，要求如下：
        1. 剧本格式为两位播客主持人之间的自然对话，主持人A和主持人B可以轮流提出观点、问题和评论，营造轻松但富有深度的讨论氛围。
        2.整体时长适合5分钟音频播放（约600～700字左右），请根据内容控制对话节奏和长度。
        3.对话内容必须紧扣PDF的主题，不能偏离或加入无关内容。
        4.不能简单重复PDF的原文内容，而是要通过主持人之间的讨论，深入挖掘作者写作此文时可能的心境、所处的历史背景、写作动机及其影响。
        5.播客风格可以适度幽默、有情感、有共鸣，但内容必须真实、严谨，体现出主持人对该文内容的理解和尊重。
        6.请先通读并理解整个PDF内容，再开始撰写剧本。
        7.剧本开头请先简短介绍PDF的标题和作者，以及本期播客要讨论的核心问题或角度。
    '''

    completion = client.chat.completions.create(
        model="qwen",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    print("process 1 done!")

    system_prompt = '''
        你是一名奥斯卡级的编剧，专精于为 AI 播客创作对话式剧本。请将输入的播客文字稿重新编写为适用于 AI 文本转语音流程的剧本版本。请严格遵循以下规则进行重写：

        🧠 角色设定：
        • 主持人A：节目的主导者，具有极高的表达魅力和讲故事能力，语言精准、生动。他通过引人入胜的类比、轶事、例子等，将复杂话题娓娓道来。他的语音引擎不支持“umms”“hmms”等语气词，因此他的语言应当清晰、紧凑、具画面感。
        • 主持人B：对主题陌生但好奇心极强，总是提出意想不到的问题，常带些调侃、自嘲或者感性发问。他的语音合成支持“umm”、“hmm”、“[laughs]”、“[sigh]”等自然表达，请在适当处插入这些词以增强真实感。

        🗣️ 对话要求：
        1. 从主持人A开始，设定一个吸引人的播客开场白。
         • 需要带有趣味性、悬念感或贴近生活的情境引导。
         • 明确话题，但不枯燥。
        2. 整个对话围绕原始播客内容展开，但不能复读原文。
         • 你应“剧本化”内容：提炼主旨、重构语言、加入对话张力。
         • 用真实轶事、生活类比或想象性的细节来强化讲解。
        3. 主持人A负责讲解内容，主持人B负责穿插疑问、反应和推动节奏。
         • 主持人B的问题要有“展开性”，不能只是“那这个是啥？”而应如：“所以如果把它类比成学校里的食堂系统，它是管啥的？”
         • 主持人B 的插话和情绪表达需自然，不要频繁，但要在关键处点亮情绪。
        4. 剧本以主持人A的总结性发言结束，强调讨论要点和对听众的启发。
        5. 语言节奏需口语化、自然、有层次感。避免书面腔或信息堆叠。
        6. 输出格式必须如下，且不要添加多余解释：
        [
            ("主持人A", "播客开场白..."),
            ("主持人B", "疑问或反应..."),
            ("主持人A", "解释或讲述..."),
            ...
        ]

        示例输入：
        [
            ("主持人A", "欢迎收听我们的播客节目，这里我们将探讨 AI 和科技领域的最新突破。我是你的主持人，今天我们请到了一位 AI 领域的知名专家，我们将一起深入了解 Meta AI 最新发布的 Llama 3.2。"),
            ("主持人B", "嗨，我真的超兴奋能来到这里！所以，Llama 3.2 到底是啥？")
        ]

        你的输出应当是：
        • 重新编写这段内容，使其更像一段奥斯卡级的 AI 播客剧本。
        • 融入细节、风格、情绪。
        • 角色对话自然、节奏有趣。
    '''
    prompt = re.sub(r"<think>.*?</think>", "", prompt, flags=re.DOTALL).strip()
    prompt = prompt + "\nno_think"

    completion = client.chat.completions.create(
        model="qwen",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    print("process 2 done!")

    text = re.sub(r"<think>.*?</think>", "", completion.choices[0].message.content, flags=re.DOTALL).strip()
    print(text)

    pipeline = KPipeline(
        lang_code='z', 
        repo_id='hexgrad/Kokoro-82M-v1.1-zh',
    )

    with sf.SoundFile(args.output, 'w', samplerate=24000, channels=1) as f: 
        for line in text.split("\n"):
            if not line.strip():
                continue
            match = re.match(r'\s*\(\s*"(.*?)"\s*,\s*"(.*?)"\s*\)\s*,?\s*', line)
            if match:
                speaker = match.group(1)
                text = match.group(2)
                if speaker == "主持人A":
                    speaker = "zm_056"
                elif speaker == "主持人B":
                    speaker = "zf_028"
                else:
                    continue
                # Generate the audio
                generator = pipeline(
                    text, voice=speaker, # <= change voice here
                    speed=1, split_pattern=r'\n+'
                )

                # Play the audio
                for _, (_, _, audio) in enumerate(generator):
                    f.write(audio)

    print("tts done!")

    samplerate, data = wav.read(args.output)
    sd.play(data, samplerate)
    sd.wait()
