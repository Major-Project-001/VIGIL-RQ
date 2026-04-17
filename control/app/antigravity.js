/**
 * antigravity.js — Vanilla Three.js port of the react-bits Antigravity effect.
 *
 * Creates a particle field with magnetic-ring attraction around the mouse cursor.
 * Particles form a glowing ring near the pointer and scatter elsewhere.
 *
 * Usage:
 *   const ag = new AntigravityEffect('#container', { count: 1000, color: '#FF9FFC' });
 *   // To destroy: ag.destroy();
 */

class AntigravityEffect {
    constructor(containerSelector, options = {}) {
        // ── Config ──
        this.count = options.count ?? 1000;
        this.magnetRadius = options.magnetRadius ?? 1;
        this.ringRadius = options.ringRadius ?? 13;
        this.waveSpeed = options.waveSpeed ?? 0.5;
        this.waveAmplitude = options.waveAmplitude ?? 1;
        this.particleSize = options.particleSize ?? 1;
        this.lerpSpeed = options.lerpSpeed ?? 0.1;
        this.color = options.color ?? '#FF9FFC';
        this.autoAnimate = options.autoAnimate ?? false;
        this.particleVariance = options.particleVariance ?? 1;
        this.rotationSpeed = options.rotationSpeed ?? 0;
        this.depthFactor = options.depthFactor ?? 1;
        this.pulseSpeed = options.pulseSpeed ?? 3;
        this.particleShape = options.particleShape ?? 'capsule';
        this.fieldStrength = options.fieldStrength ?? 10;

        // ── DOM ──
        this.container = document.querySelector(containerSelector);
        if (!this.container) {
            console.error('[Antigravity] Container not found:', containerSelector);
            return;
        }

        // ── Three.js setup ──
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 1000);
        this.camera.position.set(0, 0, 50);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setClearColor(0x000000, 0);

        // Style the renderer canvas to fill the container
        const canvas = this.renderer.domElement;
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.display = 'block';
        this.container.appendChild(canvas);

        // ── State ──
        this.mouse = { x: 0, y: 0 };
        this.virtualMouse = { x: 0, y: 0 };
        this.lastMousePos = { x: 0, y: 0 };
        this.lastMouseMoveTime = 0;
        this.clock = new THREE.Clock();
        this.destroyed = false;
        this.dummy = new THREE.Object3D();

        // ── Calculate viewport FIRST, then build particles ──
        this._resize();
        this._initParticles();
        this._initMesh();

        // ── Events ──
        this._onResize = () => {
            this._resize();
        };
        this._onMouseMove = (e) => this._handleMouseMove(e);
        this._onTouchMove = (e) => this._handleTouchMove(e);

        window.addEventListener('resize', this._onResize);
        window.addEventListener('mousemove', this._onMouseMove);
        window.addEventListener('touchmove', this._onTouchMove, { passive: true });

        // ── Start ──
        this._animate();
        console.log(`[Antigravity] Initialized with ${this.count} particles (viewport: ${this.viewportWidth.toFixed(1)}x${this.viewportHeight.toFixed(1)} world units)`);
    }

    _initParticles() {
        this.particles = [];
        const w = this.viewportWidth || 30;
        const h = this.viewportHeight || 20;

        for (let i = 0; i < this.count; i++) {
            const t = Math.random() * 100;
            const speed = 0.01 + Math.random() / 200;
            const x = (Math.random() - 0.5) * w;
            const y = (Math.random() - 0.5) * h;
            const z = (Math.random() - 0.5) * 20;
            const randomRadiusOffset = (Math.random() - 0.5) * 2;

            this.particles.push({
                t, speed, randomRadiusOffset,
                mx: x, my: y, mz: z,
                cx: x, cy: y, cz: z,
            });
        }
    }

    _initMesh() {
        let geometry;
        switch (this.particleShape) {
            case 'sphere':
                geometry = new THREE.SphereGeometry(0.2, 16, 16);
                break;
            case 'box':
                geometry = new THREE.BoxGeometry(0.3, 0.3, 0.3);
                break;
            case 'tetrahedron':
                geometry = new THREE.TetrahedronGeometry(0.3);
                break;
            case 'capsule':
            default:
                // CapsuleGeometry requires Three.js r138+.
                // Fall back to a stretched sphere if not available.
                if (typeof THREE.CapsuleGeometry === 'function') {
                    geometry = new THREE.CapsuleGeometry(0.1, 0.4, 4, 8);
                } else {
                    geometry = new THREE.SphereGeometry(0.15, 8, 8);
                    geometry.scale(1, 2.5, 1); // Approximate capsule shape
                }
                break;
        }

        const material = new THREE.MeshBasicMaterial({ color: this.color });
        this.mesh = new THREE.InstancedMesh(geometry, material, this.count);
        this.scene.add(this.mesh);
    }

    _resize() {
        const rect = this.container.getBoundingClientRect();
        const w = rect.width;
        const h = rect.height;
        if (w === 0 || h === 0) return;

        const dpr = Math.min(window.devicePixelRatio, 2);

        this.renderer.setSize(w, h);
        this.renderer.setPixelRatio(dpr);

        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();

        // Compute viewport dimensions in world units at z=0
        const vFov = (this.camera.fov * Math.PI) / 180;
        this.viewportHeight = 2 * Math.tan(vFov / 2) * this.camera.position.z;
        this.viewportWidth = this.viewportHeight * this.camera.aspect;
    }

    _handleMouseMove(e) {
        const rect = this.container.getBoundingClientRect();
        // Normalize to [-1, 1]
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
        this.lastMouseMoveTime = Date.now();
        this.lastMousePos.x = this.mouse.x;
        this.lastMousePos.y = this.mouse.y;
    }

    _handleTouchMove(e) {
        if (e.touches.length > 0) {
            const touch = e.touches[0];
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -(((touch.clientY - rect.top) / rect.height) * 2 - 1);
            this.lastMouseMoveTime = Date.now();
        }
    }

    _animate() {
        if (this.destroyed) return;
        requestAnimationFrame(() => this._animate());

        const elapsed = this.clock.getElapsedTime();
        const vw = this.viewportWidth || 30;
        const vh = this.viewportHeight || 20;

        // Target position in world coords
        let destX = (this.mouse.x * vw) / 2;
        let destY = (this.mouse.y * vh) / 2;

        // Auto-animate if idle
        if (this.autoAnimate && Date.now() - this.lastMouseMoveTime > 2000) {
            destX = Math.sin(elapsed * 0.5) * (vw / 4);
            destY = Math.cos(elapsed * 1.0) * (vh / 4);
        }

        // Smooth virtual mouse
        this.virtualMouse.x += (destX - this.virtualMouse.x) * 0.05;
        this.virtualMouse.y += (destY - this.virtualMouse.y) * 0.05;

        const targetX = this.virtualMouse.x;
        const targetY = this.virtualMouse.y;
        const globalRotation = elapsed * this.rotationSpeed;

        for (let i = 0; i < this.count; i++) {
            const p = this.particles[i];
            p.t += p.speed / 2;

            const projectionFactor = 1 - p.cz / 50;
            const projTargetX = targetX * projectionFactor;
            const projTargetY = targetY * projectionFactor;

            const dx = p.mx - projTargetX;
            const dy = p.my - projTargetY;
            const dist = Math.sqrt(dx * dx + dy * dy);

            let tx = p.mx;
            let ty = p.my;
            let tz = p.mz * this.depthFactor;

            if (dist < this.magnetRadius) {
                const angle = Math.atan2(dy, dx) + globalRotation;
                const wave = Math.sin(p.t * this.waveSpeed + angle) * (0.5 * this.waveAmplitude);
                const deviation = p.randomRadiusOffset * (5 / (this.fieldStrength + 0.1));
                const currentRingRadius = this.ringRadius + wave + deviation;

                tx = projTargetX + currentRingRadius * Math.cos(angle);
                ty = projTargetY + currentRingRadius * Math.sin(angle);
                tz = p.mz * this.depthFactor + Math.sin(p.t) * (this.waveAmplitude * this.depthFactor);
            }

            p.cx += (tx - p.cx) * this.lerpSpeed;
            p.cy += (ty - p.cy) * this.lerpSpeed;
            p.cz += (tz - p.cz) * this.lerpSpeed;

            this.dummy.position.set(p.cx, p.cy, p.cz);
            this.dummy.lookAt(projTargetX, projTargetY, p.cz);
            this.dummy.rotateX(Math.PI / 2);

            const currentDistToMouse = Math.sqrt(
                Math.pow(p.cx - projTargetX, 2) + Math.pow(p.cy - projTargetY, 2)
            );
            const distFromRing = Math.abs(currentDistToMouse - this.ringRadius);
            let scaleFactor = Math.max(0, Math.min(1, 1 - distFromRing / 10));
            const finalScale = scaleFactor * (0.8 + Math.sin(p.t * this.pulseSpeed) * 0.2 * this.particleVariance) * this.particleSize;

            this.dummy.scale.set(finalScale, finalScale, finalScale);
            this.dummy.updateMatrix();
            this.mesh.setMatrixAt(i, this.dummy.matrix);
        }

        this.mesh.instanceMatrix.needsUpdate = true;
        this.renderer.render(this.scene, this.camera);
    }

    destroy() {
        this.destroyed = true;
        window.removeEventListener('resize', this._onResize);
        window.removeEventListener('mousemove', this._onMouseMove);
        window.removeEventListener('touchmove', this._onTouchMove);
        this.renderer.dispose();
        if (this.renderer.domElement.parentNode) {
            this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
        }
    }
}
