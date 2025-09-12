import asyncio
import json
import logging
import os
import tempfile
from typing import Optional

import sys
sys.path.append("./socnv")
from sconv import BW, Ah, Ai

logger = logging.getLogger(__name__)


def _cleanup_temp_files(file_paths: list, task_id: int, is_final: bool = False):
    cleanup_type = "Final" if is_final else "Intermediate"
    logger.debug(f"{cleanup_type} cleanup for task {task_id}")
    
    files_deleted = 0
    files_failed = 0
    
    for temp_file in file_paths:
        try:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
                files_deleted += 1
                if not is_final:
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
        except Exception as e:
            files_failed += 1
            logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")
    
    if files_deleted > 0 or files_failed > 0:
        log_level = logger.debug if is_final else logger.info
        log_level(f"Task {task_id} cleanup: {files_deleted} files deleted, {files_failed} failed")
    
    if not is_final:
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            leftover_files = []
            
            for filename in os.listdir(temp_dir):
                if filename.startswith(f'task_{task_id}_') and (
                    filename.endswith('_parse.json') or 
                    filename.endswith('_refine.json') or 
                    filename.endswith('_script.py')
                ):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        os.unlink(file_path)
                        leftover_files.append(filename)
                    except Exception as e:
                        logger.warning(f"Failed to clean leftover file {filename}: {e}")
            
            if leftover_files:
                logger.info(f"Cleaned up {len(leftover_files)} leftover files for task {task_id}")
                
        except Exception as e:
            logger.warning(f"Error during leftover file cleanup for task {task_id}: {e}")


async def convert_agent_history_to_script(agent_history_path: str, task_id: int) -> Optional[str]:
    temp_parse_path = None
    temp_refine_path = None
    temp_script_path = None
    
    try:
        logger.info(f"Starting full conversion pipeline for: {agent_history_path}")
        
        temp_parse_file = tempfile.NamedTemporaryFile(mode='w', prefix=f'task_{task_id}_', suffix='_parse.json', delete=False)
        temp_refine_file = tempfile.NamedTemporaryFile(mode='w', prefix=f'task_{task_id}_', suffix='_refine.json', delete=False)
        temp_script_file = tempfile.NamedTemporaryFile(mode='w', prefix=f'task_{task_id}_', suffix='_script.py', delete=False)
        
        temp_parse_path = temp_parse_file.name
        temp_refine_path = temp_refine_file.name
        temp_script_path = temp_script_file.name
        
        temp_parse_file.close()
        temp_refine_file.close()
        temp_script_file.close()
        
        logger.info(f"Created task-specific temporary files:")
        logger.info(f"  Parse file: {temp_parse_path}")
        logger.info(f"  Refine file: {temp_refine_path}")
        logger.info(f"  Script file: {temp_script_path}")
        
        logger.info("Step 1: Parsing agent history")
        history, parsed_actions = BW(agent_history_path)
        
        with open(temp_parse_path, 'w') as f:
            json.dump(parsed_actions, f, indent=4)
        
        logger.info(f"Successfully parsed {len(parsed_actions)} actions from agent history")
        
        logger.info("Step 2: Refining action list")
        refined_actions = await Ah(temp_parse_path, temp_refine_path)
        logger.info(f"Successfully refined action list with {len(refined_actions)} actions")
        
        logger.info("Step 3: Generating script")
        script_generated = Ai(temp_refine_path, temp_script_path)
        
        logger.info(f"Script generation returned: {script_generated}")
        logger.info(f"Temp script file exists: {os.path.exists(temp_script_path)}")
        if os.path.exists(temp_script_path):
            logger.info(f"Temp script file size: {os.path.getsize(temp_script_path)} bytes")
        
        if os.path.exists(temp_script_path):
            try:
                with open(temp_script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                if script_content.strip():
                    logger.info("Full conversion pipeline completed successfully")
                    _cleanup_temp_files([temp_parse_path, temp_refine_path, temp_script_path], task_id)
                    return script_content
                else:
                    logger.error("Script file was created but is empty")
                    _cleanup_temp_files([temp_parse_path, temp_refine_path, temp_script_path], task_id)
                    return None
            except Exception as e:
                logger.error(f"Error reading script file: {e}")
                _cleanup_temp_files([temp_parse_path, temp_refine_path, temp_script_path], task_id)
                return None
        else:
            logger.error("Script generation failed or file was not created")
            logger.error(f"Expected script file at: {temp_script_path}")
            _cleanup_temp_files([temp_parse_path, temp_refine_path, temp_script_path], task_id)
            return None
        
    except Exception as e:
        logger.error(f"Error in conversion pipeline: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        _cleanup_temp_files([temp_parse_path, temp_refine_path, temp_script_path], task_id)
        return None
        
    finally:
        _cleanup_temp_files([temp_parse_path, temp_refine_path, temp_script_path], task_id, is_final=True)


async def main():
    agent_history_path = "./tmp/agent_history/task_15/task_15.json"
    
    print("🚀 Starting Script Conversion Service Test")
    print(f"📁 Input file: {agent_history_path}")
    
    if not os.path.exists(agent_history_path):
        print(f"❌ Error: File not found at {agent_history_path}")
        print("Please update the hardcoded filepath in the main() function")
        print("\nAvailable files in ./tmp/agent_history/:")
        try:
            for root, dirs, files in os.walk("./tmp/agent_history/"):
                for file in files:
                    if file.endswith('.json'):
                        print(f"  - {os.path.join(root, file)}")
        except Exception as e:
            print(f"  Could not list files: {e}")
        return
    
    try:
        task_id = 15
        script_content = await convert_agent_history_to_script(agent_history_path, task_id)
        
        if script_content:
            output_path = "./tmp/generated_script.py"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"✅ Script generated successfully!")
            print(f"📄 Output saved to: {output_path}")
            print(f"📊 Script length: {len(script_content)} characters")
            
            print("\n📋 Script preview (first 10 lines):")
            lines = script_content.split('\n')[:10]
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}: {line}")
            
            if len(script_content.split('\n')) > 10:
                print("   ...")
                total_lines = len(script_content.split('\n'))
                print(f"   (Total: {total_lines} lines)")
                
        else:
            print("❌ Script generation failed!")
            
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())

