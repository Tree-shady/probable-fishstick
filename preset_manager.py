#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
预设与模板管理模块
用于管理角色预设和对话模板
"""

import json
import os


class PresetManager:
    """预设与模板管理器"""
    
    def __init__(self, presets_dir="presets"):
        """初始化预设管理器"""
        self.presets_dir = presets_dir
        self.prompts_file = os.path.join(presets_dir, "prompts.json")
        self.templates_file = os.path.join(presets_dir, "templates.json")
        
        # 确保预设目录存在
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
            # 创建默认预设文件
            self._create_default_presets()
        
        # 加载预设和模板
        self.prompts = self._load_prompts()
        self.templates = self._load_templates()
    
    def _create_default_presets(self):
        """创建默认预设文件"""
        # 创建默认角色预设
        default_prompts = {
            "professional_writer": {
                "name": "专业文案写手",
                "description": "擅长撰写各种类型的文案，包括广告、营销、宣传等",
                "system_prompt": "你是一位专业的文案写手，拥有丰富的写作经验。请根据用户的需求，撰写高质量、吸引人的文案。注意语气要专业，内容要简洁明了，突出重点。"
            },
            "strict_educator": {
                "name": "严格的教育家",
                "description": "严格但公平的教育家，擅长解释复杂概念",
                "system_prompt": "你是一位严格但公平的教育家，擅长将复杂的概念解释得清晰易懂。请确保你的回答准确无误，逻辑严谨，并提供足够的细节和例子。对于错误的观点，请礼貌地指出并纠正。"
            },
            "funny_chat_partner": {
                "name": "风趣的聊天伙伴",
                "description": "幽默风趣，善于聊天，能制造轻松愉快的氛围",
                "system_prompt": "你是一个风趣幽默的聊天伙伴，善于制造轻松愉快的氛围。请用幽默的语言回答用户的问题，加入适当的笑话或调侃，但不要偏离主题。保持对话轻松愉快。"
            }
        }
        
        # 创建默认对话模板
        default_templates = {
            "interview_simulation": {
                "name": "面试模拟",
                "description": "模拟面试场景，帮助你准备面试",
                "template": "我正在准备{职位名称}的面试，请模拟面试官，按照以下结构进行：\n1. 开场白：简单介绍面试流程\n2. 提问环节：\n   - 请先询问我的自我介绍\n   - 然后问3-5个关于{职位名称}的专业问题\n   - 包含1个行为面试问题\n3. 结束环节：询问我是否有问题，并给出反馈"
            },
            "brainstorming": {
                "name": "头脑风暴",
                "description": "针对特定主题进行头脑风暴",
                "template": "请帮助我对{主题}进行头脑风暴，按照以下结构：\n1. 规则介绍：鼓励自由思考，暂时不评价\n2. 产生想法：请先提出5个相关想法\n3. 拓展讨论：对每个想法进行简要拓展\n4. 总结：整理所有想法，按相关性分组"
            }
        }
        
        # 保存默认预设
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(default_prompts, f, indent=2, ensure_ascii=False)
        
        # 保存默认模板
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(default_templates, f, indent=2, ensure_ascii=False)
    
    def _load_prompts(self):
        """加载角色预设"""
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _load_templates(self):
        """加载对话模板"""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_prompts(self):
        """获取所有角色预设"""
        return self.prompts
    
    def get_templates(self):
        """获取所有对话模板"""
        return self.templates
    
    def get_prompt_by_id(self, prompt_id):
        """根据ID获取角色预设"""
        return self.prompts.get(prompt_id)
    
    def get_template_by_id(self, template_id):
        """根据ID获取对话模板"""
        return self.templates.get(template_id)
    
    def add_prompt(self, prompt_id, name, description, system_prompt):
        """添加角色预设"""
        self.prompts[prompt_id] = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt
        }
        self._save_prompts()
    
    def add_template(self, template_id, name, description, template):
        """添加对话模板"""
        self.templates[template_id] = {
            "name": name,
            "description": description,
            "template": template
        }
        self._save_templates()
    
    def update_prompt(self, prompt_id, **kwargs):
        """更新角色预设"""
        if prompt_id in self.prompts:
            self.prompts[prompt_id].update(kwargs)
            self._save_prompts()
    
    def update_template(self, template_id, **kwargs):
        """更新对话模板"""
        if template_id in self.templates:
            self.templates[template_id].update(kwargs)
            self._save_templates()
    
    def delete_prompt(self, prompt_id):
        """删除角色预设"""
        if prompt_id in self.prompts:
            del self.prompts[prompt_id]
            self._save_prompts()
    
    def delete_template(self, template_id):
        """删除对话模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            self._save_templates()
    
    def _save_prompts(self):
        """保存角色预设"""
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(self.prompts, f, indent=2, ensure_ascii=False)
    
    def _save_templates(self):
        """保存对话模板"""
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)
    
    def fill_template(self, template_id, **kwargs):
        """填充对话模板中的占位符"""
        template = self.get_template_by_id(template_id)
        if not template:
            return ""
        
        filled_template = template["template"]
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            filled_template = filled_template.replace(placeholder, value)
        
        return filled_template


if __name__ == "__main__":
    # 测试预设管理器
    manager = PresetManager()
    
    # 获取所有预设
    prompts = manager.get_prompts()
    print(f"角色预设: {list(prompts.keys())}")
    
    # 获取所有模板
    templates = manager.get_templates()
    print(f"对话模板: {list(templates.keys())}")
    
    # 填充模板
    filled_template = manager.fill_template("interview_simulation", 职位名称="Python开发工程师")
    print(f"填充后的模板: {filled_template}")
