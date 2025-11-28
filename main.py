import os
import logging

from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from ragie_client import get_ragie_client, RagieClient, RagieError
from generator import get_generator, ContentGenerator
from critic import get_critic, ContentCritic
from persona import get_persona_manager, PersonaManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


def get_api_status() -> dict:
    status = {
        "ragie": False,
        "deepseek": False
    }
    
    try:
        if os.environ.get("RAGIE_API_KEY"):
            status["ragie"] = True
    except Exception:
        pass
    
    try:
        if os.environ.get("DEEPSEEK_API_KEY"):
            status["deepseek"] = True
    except Exception:
        pass
    
    return status


@app.route('/')
def index():
    persona_manager = get_persona_manager()
    personas = persona_manager.get_all_personas()
    api_status = get_api_status()
    return render_template('index.html', personas=personas, api_status=api_status)


@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        persona_id = data.get('persona', 'professional_writer')
        custom_prompt = data.get('custom_prompt', '')
        use_ragie = data.get('use_ragie', False)
        ragie_query = data.get('ragie_query', '')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))
        
        if not prompt:
            return jsonify({"success": False, "error": "Prompt is required"}), 400
        
        persona_manager = get_persona_manager()
        system_prompt = persona_manager.get_persona_prompt(persona_id, custom_prompt)
        
        context = None
        ragie_error = None
        if use_ragie and ragie_query:
            try:
                ragie_client = get_ragie_client()
                context = ragie_client.get_context(ragie_query)
                if not context:
                    context = None
            except RagieError as e:
                logger.warning(f"Ragie context retrieval failed: {e}")
                ragie_error = str(e)
                context = None
            except Exception as e:
                logger.warning(f"Unexpected error retrieving context: {e}")
                ragie_error = str(e)
                context = None
        
        generator = get_generator()
        result = generator.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if result["success"]:
            response_data = {
                "success": True,
                "content": result["content"],
                "usage": result["usage"],
                "context_used": context is not None and len(context) > 0
            }
            if ragie_error:
                response_data["ragie_warning"] = ragie_error
            return jsonify(response_data)
        else:
            return jsonify({"success": False, "error": result.get("error", "Generation failed")}), 500
            
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/critique', methods=['POST'])
def api_critique():
    try:
        data = request.json
        content = data.get('content', '')
        original_prompt = data.get('original_prompt', '')
        focus_areas = data.get('focus_areas', [])
        
        if not content:
            return jsonify({"success": False, "error": "Content is required"}), 400
        
        critic = get_critic()
        result = critic.critique(
            content=content,
            context=original_prompt,
            focus_areas=focus_areas if focus_areas else None
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "critique": result["critique"],
                "usage": result["usage"]
            })
        else:
            return jsonify({"success": False, "error": result.get("error", "Critique failed")}), 500
            
    except Exception as e:
        logger.error(f"Critique error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/refine', methods=['POST'])
def api_refine():
    try:
        data = request.json
        original_content = data.get('original_content', '')
        critique = data.get('critique', '')
        instructions = data.get('instructions', '')
        
        if not original_content or not critique:
            return jsonify({"success": False, "error": "Content and critique are required"}), 400
        
        critic = get_critic()
        result = critic.refine(
            original_content=original_content,
            critique=critique,
            instructions=instructions
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "refined_content": result["refined_content"],
                "usage": result["usage"]
            })
        else:
            return jsonify({"success": False, "error": result.get("error", "Refinement failed")}), 500
            
    except Exception as e:
        logger.error(f"Refine error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/retrieve', methods=['POST'])
def api_retrieve():
    try:
        data = request.json
        query = data.get('query', '')
        top_k = int(data.get('top_k', 5))
        
        if not query:
            return jsonify({"success": False, "error": "Query is required"}), 400
        
        ragie_client = get_ragie_client()
        context = ragie_client.get_context(query, top_k=top_k)
        
        return jsonify({
            "success": True,
            "context": context
        })
            
    except Exception as e:
        logger.error(f"Retrieve error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/personas', methods=['GET'])
def api_personas():
    persona_manager = get_persona_manager()
    personas = persona_manager.get_all_personas()
    return jsonify({"success": True, "personas": personas})


@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify(get_api_status())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
