
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Visual Content Capture
Captura de screenshots e conteúdo visual usando Selenium
"""

import os
import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class VisualContentCapture:
    """Capturador de conteúdo visual usando Selenium"""

    def __init__(self):
        """Inicializa o capturador visual"""
        self.driver = None
        self.wait_timeout = 10
        self.page_load_timeout = 30
        
        logger.info("📸 Visual Content Capture inicializado")
        
        # API keys para busca no Google Images
        self.serper_api_keys = self._load_serper_keys()
        self.current_serper_index = 0

    def _load_serper_keys(self) -> list:
        """Carrega chaves da API Serper para busca de imagens"""
        keys = []
        
        # Chave principal
        main_key = os.getenv('SERPER_API_KEY')
        if main_key:
            keys.append(main_key)
        
        # Chaves numeradas
        counter = 1
        while True:
            numbered_key = os.getenv(f'SERPER_API_KEY_{counter}')
            if numbered_key:
                keys.append(numbered_key)
                counter += 1
            else:
                break
        
        logger.info(f"✅ {len(keys)} chaves Serper carregadas para busca de imagens")
        return keys

    def _get_next_serper_key(self) -> Optional[str]:
        """Obtém próxima chave Serper com rotação"""
        if not self.serper_api_keys:
            return None
            
        key = self.serper_api_keys[self.current_serper_index]
        self.current_serper_index = (self.current_serper_index + 1) % len(self.serper_api_keys)
        return key

    def _try_google_images_extraction(self, post_url: str, filename: str, session_dir: Path) -> Dict[str, Any]:
        """
        PROCEDIMENTO PRIORITÁRIO: Busca imagem no Google Images
        Implementa exatamente o procedimento descrito no anexo com melhorias
        """
        try:
            logger.info(f"🔍 PRIORIDADE 1: Buscando imagem no Google Images para {post_url}")
            
            # Prepara múltiplas queries para aumentar chance de sucesso
            queries = [
                post_url,  # URL completa
                post_url.replace('https://', '').replace('http://', ''),  # Sem protocolo
                f'"{post_url}"',  # Com aspas
                f'site:instagram.com {post_url.split("/")[-2] if "/" in post_url else post_url}'  # Estratégia alternativa
            ]
            
            for i, query in enumerate(queries, 1):
                logger.info(f"🔍 Tentativa {i}/{len(queries)} com query: {query}")
                
                # Usa API Serper para buscar imagens
                api_key = self._get_next_serper_key()
                if not api_key:
                    logger.warning("⚠️ Nenhuma chave Serper disponível")
                    continue
                
                import requests
                
                url = "https://google.serper.dev/images"
                payload = {
                    "q": query,
                    "num": 10,  # Busca 10 imagens para ter mais alternativas
                    "safe": "off",
                    "gl": "br",
                    "hl": "pt-br",
                    "imgSize": "large",
                    "imgType": "photo"
                }
                headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
                
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        images = data.get('images', [])
                        
                        logger.info(f"📊 Google Images retornou {len(images)} imagens para query {i}")
                        
                        # Tenta baixar cada imagem até conseguir uma
                        for j, image in enumerate(images, 1):
                            image_url = image.get('imageUrl')
                            if not image_url:
                                continue
                                
                            logger.info(f"⬇️ Tentando baixar imagem {j}: {image_url[:100]}...")
                            
                            success = self._download_image_from_url(image_url, f"{filename}_{i}_{j}", session_dir)
                            if success:
                                # Procura o arquivo baixado
                                for ext in ['.jpg', '.png', '.webp', '.jpeg']:
                                    screenshot_path = session_dir / f"{filename}_{i}_{j}{ext}"
                                    if screenshot_path.exists():
                                        logger.info(f"✅ SUCESSO: Imagem baixada via Google Images: {screenshot_path}")
                                        
                                        # Renomeia para nome padrão
                                        final_path = session_dir / f"{filename}{ext}"
                                        screenshot_path.rename(final_path)
                                        
                                        return {
                                            'success': True,
                                            'url': post_url,
                                            'image_source': image_url,
                                            'title': f"Imagem extraída do Google Images (Query {i})",
                                            'description': f"Imagem encontrada via busca no Google Images",
                                            'filename': final_path.name,
                                            'filepath': str(final_path),
                                            'filesize': final_path.stat().st_size,
                                            'method': 'google_images_search',
                                            'query_used': query,
                                            'image_position': j,
                                            'timestamp': datetime.now().isoformat()
                                        }
                            
                            # Rate limiting entre tentativas
                            time.sleep(0.3)
                    
                    elif response.status_code == 429:
                        logger.warning("⚠️ Rate limit Serper - aguardando 2s...")
                        time.sleep(2)
                        continue
                    else:
                        logger.warning(f"⚠️ Status {response.status_code} para query {i}")
                
                except requests.RequestException as e:
                    logger.warning(f"⚠️ Erro de rede na query {i}: {e}")
                    continue
                
                # Pausa entre queries
                time.sleep(1)
            
            logger.warning("⚠️ Todas as tentativas do Google Images falharam")
            
        except Exception as e:
            logger.error(f"❌ Erro crítico no Google Images: {str(e)}")
        
        return {'success': False, 'error': 'Google Images search failed after all attempts'}

    def _download_image_from_url(self, image_url: str, filename: str, session_dir: Path) -> bool:
        """Baixa imagem da URL com validação robusta e múltiplas tentativas"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"⬇️ Tentativa {attempt + 1}/{max_attempts} de download: {image_url[:100]}...")
                
                import requests
                
                # Headers mais robustos para evitar bloqueios
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'image',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site'
                }
                
                # Timeout progressivo
                timeout = 15 + (attempt * 10)  # 15, 25, 35 segundos
                
                response = requests.get(
                    image_url, 
                    headers=headers, 
                    timeout=timeout, 
                    stream=True,
                    allow_redirects=True,
                    verify=True
                )
                
                response.raise_for_status()
                
                # Verifica Content-Type
                content_type = response.headers.get('content-type', '').lower()
                logger.info(f"📄 Content-Type: {content_type}")
                
                # CORREÇÃO: Verifica se está recebendo HTML em vez de imagem
                if 'text/html' in content_type or 'text/plain' in content_type:
                    logger.warning(f"⚠️ Recebendo HTML/texto em vez de imagem: {content_type}")
                    # Lê uma pequena amostra para confirmar
                    sample = response.content[:500].decode('utf-8', errors='ignore').lower()
                    if '<html' in sample or '<!doctype' in sample or '<body' in sample:
                        logger.warning(f"⚠️ Confirmado: resposta é HTML, não imagem. Pulando...")
                        continue  # Tenta próxima tentativa
                
                # Verifica se Content-Type é de imagem válida
                valid_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/svg+xml']
                if not any(img_type in content_type for img_type in valid_image_types):
                    logger.warning(f"⚠️ Content-Type não é de imagem válida: {content_type}")
                    # Se não tem Content-Type de imagem, verifica pela URL
                    if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        logger.warning(f"⚠️ URL também não parece ser de imagem. Pulando...")
                        continue
                
                # Determina extensão baseada no Content-Type e URL
                extension = '.jpg'  # Default
                if 'jpeg' in content_type or 'jpg' in content_type:
                    extension = '.jpg'
                elif 'png' in content_type:
                    extension = '.png'
                elif 'webp' in content_type:
                    extension = '.webp'
                elif 'gif' in content_type:
                    extension = '.gif'
                elif image_url.lower().endswith('.png'):
                    extension = '.png'
                elif image_url.lower().endswith('.webp'):
                    extension = '.webp'
                elif image_url.lower().endswith('.gif'):
                    extension = '.gif'
                
                image_path = session_dir / f"{filename}{extension}"
                
                # Download com validação de tamanho
                total_size = 0
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                            total_size += len(chunk)
                            
                            # Limite de 50MB para evitar downloads gigantes
                            if total_size > 50 * 1024 * 1024:
                                logger.warning("⚠️ Arquivo muito grande (>50MB), abortando")
                                raise Exception("Arquivo muito grande")
                
                # Validação final
                if image_path.exists():
                    file_size = image_path.stat().st_size
                    logger.info(f"📊 Arquivo baixado: {file_size:,} bytes")
                    
                    # Verifica tamanho mínimo (3KB) e máximo (50MB)
                    if 3000 <= file_size <= 50 * 1024 * 1024:
                        # Validação adicional: tenta ler o início do arquivo para verificar se é uma imagem
                        try:
                            with open(image_path, 'rb') as f:
                                header = f.read(50)
                                
                            # CORREÇÃO: Verifica primeiro se é HTML
                            header_text = header.decode('utf-8', errors='ignore').lower()
                            if '<html' in header_text or '<!doctype' in header_text or '<body' in header_text:
                                logger.warning(f"⚠️ Arquivo baixado é HTML, não imagem!")
                                image_path.unlink()  # Remove arquivo inválido
                                continue  # Tenta próxima tentativa
                            
                            # Assinaturas de arquivos de imagem
                            image_signatures = [
                                b'\xff\xd8\xff',  # JPEG
                                b'\x89PNG\r\n\x1a\n',  # PNG
                                b'GIF8',  # GIF
                                b'RIFF',  # WebP (starts with RIFF)
                                b'<svg',  # SVG
                                b'BM',    # BMP
                                b'\x00\x00\x01\x00',  # ICO
                            ]
                            
                            is_valid_image = any(header.startswith(sig) for sig in image_signatures)
                            
                            if is_valid_image:
                                logger.info(f"✅ DOWNLOAD SUCESSO: {image_path} ({file_size:,} bytes)")
                                return True
                            else:
                                logger.warning(f"⚠️ Arquivo não parece ser uma imagem válida (assinatura não reconhecida)")
                                logger.info(f"🔍 Primeiros bytes: {header[:20]}")
                                image_path.unlink()  # Remove arquivo inválido
                        except Exception as e:
                            logger.warning(f"⚠️ Erro na validação da imagem: {e}")
                            
                    else:
                        logger.warning(f"⚠️ Tamanho inválido: {file_size} bytes (mín: 3KB, máx: 50MB)")
                        if image_path.exists():
                            image_path.unlink()
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout na tentativa {attempt + 1}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🌐 Erro de conexão na tentativa {attempt + 1}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"📡 Erro HTTP {e.response.status_code} na tentativa {attempt + 1}")
                # Se for 404, 403, ou similar, não vale a pena tentar novamente
                if e.response.status_code in [404, 403, 401, 410]:
                    break
            except Exception as e:
                logger.warning(f"❌ Erro na tentativa {attempt + 1}: {str(e)}")
            
            # Pausa entre tentativas (backoff exponencial)
            if attempt < max_attempts - 1:
                sleep_time = 2 ** attempt  # 1s, 2s, 4s
                logger.info(f"⏳ Aguardando {sleep_time}s antes da próxima tentativa...")
                time.sleep(sleep_time)
        
        logger.error(f"❌ FALHA TOTAL: Não foi possível baixar a imagem após {max_attempts} tentativas")
        return False

    def _setup_driver(self) -> webdriver.Chrome:
        """Configura o driver do Chrome em modo headless"""
        try:
            chrome_options = Options()
            
            # Configurações para modo headless e otimização no Replit
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Para economizar banda
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            
            # Correções para erros específicos de GPU, WebGL e GCM
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-webgl2")
            chrome_options.add_argument("--disable-3d-apis")
            chrome_options.add_argument("--disable-accelerated-2d-canvas")
            chrome_options.add_argument("--disable-accelerated-jpeg-decoding")
            chrome_options.add_argument("--disable-accelerated-mjpeg-decode")
            chrome_options.add_argument("--disable-accelerated-video-decode")
            chrome_options.add_argument("--disable-accelerated-video-encode")
            chrome_options.add_argument("--disable-gpu-sandbox")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-pings")
            chrome_options.add_argument("--no-zygote")
            chrome_options.add_argument("--single-process")  # Força processo único para evitar problemas de GPU
            
            # Usa selenium_checker para configuração robusta
            from .selenium_checker import selenium_checker
            
            # Executa verificação completa
            check_results = selenium_checker.full_check()
            
            if not check_results['selenium_ready']:
                raise Exception("Selenium não está configurado corretamente")
            
            # Configura o Chrome com o melhor caminho encontrado
            best_chrome_path = check_results['best_chrome_path']
            if best_chrome_path:
                chrome_options.binary_location = best_chrome_path
                logger.info(f"✅ Chrome configurado: {best_chrome_path}")
            
            # Tenta usar ChromeDriverManager primeiro
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ ChromeDriverManager funcionou")
            except Exception as e:
                logger.warning(f"⚠️ ChromeDriverManager falhou: {e}, usando chromedriver do sistema")
                # Fallback para chromedriver do sistema
                driver = webdriver.Chrome(options=chrome_options)
            
            driver.set_page_load_timeout(self.page_load_timeout)
            
            logger.info("✅ Chrome driver configurado com sucesso")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Chrome driver: {e}")
            raise

    def _create_session_directory(self, session_id: str) -> Path:
        """Cria diretório para a sessão"""
        try:
            session_dir = Path("analyses_data") / "files" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📁 Diretório criado: {session_dir}")
            return session_dir
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretório: {e}")
            raise

    def _take_screenshot(self, url: str, filename: str, session_dir: Path) -> Dict[str, Any]:
        """Captura screenshot com PRIORIDADE para Google Images"""
        
        # PRIORIDADE 1: SEMPRE tenta Google Images primeiro (para qualquer URL)
        logger.info(f"🎯 ESTRATÉGIA PRIORITÁRIA: Google Images para {url}")
        google_image_result = self._try_google_images_extraction(url, filename, session_dir)
        if google_image_result and google_image_result.get('success'):
            logger.info(f"✅ SUCESSO VIA GOOGLE IMAGES: {url}")
            return google_image_result
        
        # PRIORIDADE 2: Screenshot tradicional apenas se Google Images falhar
        logger.info(f"🔄 FALLBACK: Screenshot tradicional para {url}")
        
        try:
            logger.info(f"📸 Capturando screenshot: {url}")
            
            # Acessa a URL
            self.driver.get(url)
            
            # Aguarda o carregamento da página
            try:
                WebDriverWait(self.driver, self.wait_timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"⚠️ Timeout aguardando carregamento de {url}")
            
            # Aguarda um pouco mais para renderização completa
            time.sleep(2)
            
            # Captura informações da página
            page_title = self.driver.title or "Sem título"
            page_url = self.driver.current_url
            
            # Tenta obter meta description
            meta_description = ""
            try:
                meta_element = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                meta_description = meta_element.get_attribute("content") or ""
            except:
                pass
            
            # Define o caminho do arquivo
            screenshot_path = session_dir / f"{filename}.png"
            
            # Captura o screenshot
            self.driver.save_screenshot(str(screenshot_path))
            
            # Verifica se o arquivo foi criado
            if screenshot_path.exists() and screenshot_path.stat().st_size > 0:
                logger.info(f"✅ Screenshot salvo: {screenshot_path}")
                
                return {
                    'success': True,
                    'url': url,
                    'final_url': page_url,
                    'title': page_title,
                    'description': meta_description,
                    'filename': f"{filename}.png",
                    'filepath': str(screenshot_path),
                    'filesize': screenshot_path.stat().st_size,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception("Screenshot não foi criado ou está vazio")
                
        except Exception as e:
            error_msg = f"Erro ao capturar screenshot de {url}: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'url': url,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

    async def capture_screenshots(self, urls: List[str], session_id: str) -> Dict[str, Any]:
        """
        Captura screenshots de uma lista de URLs
        
        Args:
            urls: Lista de URLs para capturar
            session_id: ID da sessão para organização
        """
        logger.info(f"📸 Iniciando captura de {len(urls)} screenshots para sessão {session_id}")
        
        # Resultado da operação
        capture_results = {
            'session_id': session_id,
            'total_urls': len(urls),
            'successful_captures': 0,
            'failed_captures': 0,
            'screenshots': [],
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'session_directory': None
        }
        
        try:
            # Cria diretório da sessão
            session_dir = self._create_session_directory(session_id)
            capture_results['session_directory'] = str(session_dir)
            
            # Configura o driver
            self.driver = self._setup_driver()
            
            # Processa cada URL
            for i, url in enumerate(urls, 1):
                if not url or not url.startswith(('http://', 'https://')):
                    logger.warning(f"⚠️ URL inválida ignorada: {url}")
                    capture_results['failed_captures'] += 1
                    capture_results['errors'].append(f"URL inválida: {url}")
                    continue
                
                try:
                    # Gera nome do arquivo
                    filename = f"screenshot_{i:03d}"
                    
                    # Captura o screenshot
                    result = self._take_screenshot(url, filename, session_dir)
                    
                    if result['success']:
                        capture_results['successful_captures'] += 1
                        capture_results['screenshots'].append(result)
                    else:
                        capture_results['failed_captures'] += 1
                        capture_results['errors'].append(result['error'])
                    
                    # Pequena pausa entre capturas para não sobrecarregar
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Erro processando URL {url}: {e}"
                    logger.error(f"❌ {error_msg}")
                    capture_results['failed_captures'] += 1
                    capture_results['errors'].append(error_msg)
            
            # Finaliza a captura
            capture_results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"✅ Captura concluída: {capture_results['successful_captures']}/{capture_results['total_urls']} sucessos")
            
        except Exception as e:
            error_msg = f"Erro crítico na captura: {e}"
            logger.error(f"❌ {error_msg}")
            capture_results['critical_error'] = error_msg
            
        finally:
            # Fecha o driver se estiver aberto
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("✅ Chrome driver fechado")
                except Exception as e:
                    logger.error(f"❌ Erro ao fechar driver: {e}")
                self.driver = None
        
        return capture_results

    def select_top_urls(self, all_results: Dict[str, Any], max_urls: int = 10) -> List[str]:
        """
        Seleciona as URLs mais relevantes dos resultados de busca
        
        Args:
            all_results: Resultados consolidados de todas as buscas
            max_urls: Número máximo de URLs para retornar
        """
        logger.info(f"🎯 Selecionando top {max_urls} URLs mais relevantes")
        
        # Verifica se all_results é um dicionário ou lista
        if isinstance(all_results, dict):
            all_urls = all_results.get('consolidated_urls', [])
        elif isinstance(all_results, list):
            all_urls = all_results
        else:
            all_urls = []
        
        if not all_urls:
            logger.warning("⚠️ Nenhuma URL encontrada nos resultados")
            return []
        
        # Por enquanto, retorna as primeiras URLs únicas
        # Em uma implementação mais sofisticada, poderia ranquear por relevância
        unique_urls = []
        seen_domains = set()
        
        for url in all_urls:
            try:
                # Extrai domínio para diversificar
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.lower()
                
                # Adiciona URL se for de domínio novo ou se ainda não temos URLs suficientes
                if domain not in seen_domains or len(unique_urls) < max_urls // 2:
                    unique_urls.append(url)
                    seen_domains.add(domain)
                    
                    if len(unique_urls) >= max_urls:
                        break
                        
            except Exception as e:
                logger.warning(f"⚠️ Erro processando URL {url}: {e}")
                continue
        
        logger.info(f"✅ Selecionadas {len(unique_urls)} URLs de {len(seen_domains)} domínios diferentes")
        return unique_urls

    def cleanup_old_screenshots(self, days_old: int = 7):
        """Remove screenshots antigos para economizar espaço"""
        try:
            files_dir = Path("analyses_data") / "files"
            if not files_dir.exists():
                return
            
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            removed_count = 0
            
            for session_dir in files_dir.iterdir():
                if session_dir.is_dir():
                    for screenshot in session_dir.glob("*.png"):
                        if screenshot.stat().st_mtime < cutoff_time:
                            screenshot.unlink()
                            removed_count += 1
                    
                    # Remove diretório se estiver vazio
                    try:
                        session_dir.rmdir()
                    except OSError:
                        pass  # Diretório não está vazio
            
            if removed_count > 0:
                logger.info(f"🧹 Removidos {removed_count} screenshots antigos")
                
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")

# Instância global
visual_content_capture = VisualContentCapture()
