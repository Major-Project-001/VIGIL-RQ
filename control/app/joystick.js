/**
 * joystick.js — Canvas-based virtual touch joystick for VIGIL-RQ controller.
 *
 * Renders a circular joystick track with a draggable knob. Returns normalised
 * (x, y) values in the range [-1, 1]. Auto-centers on touch release.
 *
 * Usage:
 *   const joystick = new VirtualJoystick('joystickCanvas', (x, y) => {
 *       console.log(`Joystick: x=${x}, y=${y}`);
 *   });
 */

class VirtualJoystick {
    /**
     * @param {string} canvasId — ID of the canvas element
     * @param {function(number, number)} onChange — Callback with (x, y) in [-1, 1]
     */
    constructor(canvasId, onChange) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.onChange = onChange || (() => {});

        // Joystick state
        this.knobX = 0;   // Normalised: -1 to +1
        this.knobY = 0;
        this.isDragging = false;
        this.touchId = null;

        // Dimensions (recalculated on resize)
        this._updateDimensions();

        // Bind events
        this.canvas.addEventListener('touchstart', (e) => this._onTouchStart(e), { passive: false });
        this.canvas.addEventListener('touchmove', (e) => this._onTouchMove(e), { passive: false });
        this.canvas.addEventListener('touchend', (e) => this._onTouchEnd(e));
        this.canvas.addEventListener('touchcancel', (e) => this._onTouchEnd(e));

        // Mouse fallback (for desktop testing)
        this.canvas.addEventListener('mousedown', (e) => this._onMouseDown(e));
        window.addEventListener('mousemove', (e) => this._onMouseMove(e));
        window.addEventListener('mouseup', (e) => this._onMouseUp(e));

        // Resize handling
        window.addEventListener('resize', () => {
            this._updateDimensions();
            this._draw();
        });

        // Initial draw
        this._draw();
    }

    _updateDimensions() {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);

        this.centerX = rect.width / 2;
        this.centerY = rect.height / 2;
        this.trackRadius = Math.min(rect.width, rect.height) / 2 - 10;
        this.knobRadius = this.trackRadius * 0.3;
        this.displayWidth = rect.width;
        this.displayHeight = rect.height;
    }

    _draw() {
        const ctx = this.ctx;
        const w = this.displayWidth;
        const h = this.displayHeight;

        ctx.clearRect(0, 0, w, h);

        // Track ring
        ctx.beginPath();
        ctx.arc(this.centerX, this.centerY, this.trackRadius, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Cross-hair guides
        ctx.beginPath();
        ctx.moveTo(this.centerX, this.centerY - this.trackRadius * 0.7);
        ctx.lineTo(this.centerX, this.centerY + this.trackRadius * 0.7);
        ctx.moveTo(this.centerX - this.trackRadius * 0.7, this.centerY);
        ctx.lineTo(this.centerX + this.trackRadius * 0.7, this.centerY);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Knob position in pixels
        const knobPxX = this.centerX + this.knobX * this.trackRadius;
        const knobPxY = this.centerY - this.knobY * this.trackRadius; // Y inverted

        // Knob glow
        if (this.isDragging) {
            const glow = ctx.createRadialGradient(
                knobPxX, knobPxY, 0,
                knobPxX, knobPxY, this.knobRadius * 2
            );
            glow.addColorStop(0, 'rgba(56, 189, 248, 0.3)');
            glow.addColorStop(1, 'rgba(56, 189, 248, 0)');
            ctx.fillStyle = glow;
            ctx.fillRect(0, 0, w, h);
        }

        // Connection line (center to knob)
        if (this.knobX !== 0 || this.knobY !== 0) {
            ctx.beginPath();
            ctx.moveTo(this.centerX, this.centerY);
            ctx.lineTo(knobPxX, knobPxY);
            ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        // Knob circle
        ctx.beginPath();
        ctx.arc(knobPxX, knobPxY, this.knobRadius, 0, Math.PI * 2);

        const gradient = ctx.createRadialGradient(
            knobPxX - 3, knobPxY - 3, 0,
            knobPxX, knobPxY, this.knobRadius
        );
        gradient.addColorStop(0, this.isDragging ? '#60cdff' : '#4ba8d4');
        gradient.addColorStop(1, this.isDragging ? '#38bdf8' : '#2a8ab8');
        ctx.fillStyle = gradient;
        ctx.fill();

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Direction labels
        ctx.fillStyle = 'rgba(148, 163, 184, 0.3)';
        ctx.font = '500 9px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('FWD', this.centerX, 14);
        ctx.fillText('BWD', this.centerX, h - 6);
        ctx.textAlign = 'left';
        ctx.fillText('L', 6, this.centerY + 3);
        ctx.textAlign = 'right';
        ctx.fillText('R', w - 6, this.centerY + 3);
    }

    _getPosition(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const dx = (clientX - rect.left - this.centerX) / this.trackRadius;
        const dy = -(clientY - rect.top - this.centerY) / this.trackRadius; // Invert Y

        // Clamp to unit circle
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > 1) {
            return { x: dx / dist, y: dy / dist };
        }
        return { x: dx, y: dy };
    }

    _update(x, y) {
        this.knobX = Math.round(x * 100) / 100;
        this.knobY = Math.round(y * 100) / 100;
        this._draw();
        this.onChange(this.knobX, this.knobY);
    }

    _release() {
        this.isDragging = false;
        this.touchId = null;

        // Smooth return to center
        const animate = () => {
            this.knobX *= 0.7;
            this.knobY *= 0.7;

            if (Math.abs(this.knobX) < 0.01 && Math.abs(this.knobY) < 0.01) {
                this.knobX = 0;
                this.knobY = 0;
                this._draw();
                this.onChange(0, 0);
                return;
            }

            this._draw();
            this.onChange(this.knobX, this.knobY);
            requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }

    // ── Touch events ──
    _onTouchStart(e) {
        e.preventDefault();
        if (this.isDragging) return;

        const touch = e.changedTouches[0];
        this.isDragging = true;
        this.touchId = touch.identifier;

        const pos = this._getPosition(touch.clientX, touch.clientY);
        this._update(pos.x, pos.y);

        // Haptic feedback
        if (navigator.vibrate) navigator.vibrate(15);
    }

    _onTouchMove(e) {
        e.preventDefault();
        if (!this.isDragging) return;

        for (const touch of e.changedTouches) {
            if (touch.identifier === this.touchId) {
                const pos = this._getPosition(touch.clientX, touch.clientY);
                this._update(pos.x, pos.y);
                break;
            }
        }
    }

    _onTouchEnd(e) {
        for (const touch of e.changedTouches) {
            if (touch.identifier === this.touchId) {
                this._release();
                break;
            }
        }
    }

    // ── Mouse events (desktop fallback) ──
    _onMouseDown(e) {
        this.isDragging = true;
        const pos = this._getPosition(e.clientX, e.clientY);
        this._update(pos.x, pos.y);
    }

    _onMouseMove(e) {
        if (!this.isDragging) return;
        const pos = this._getPosition(e.clientX, e.clientY);
        this._update(pos.x, pos.y);
    }

    _onMouseUp(e) {
        if (this.isDragging) {
            this._release();
        }
    }
}
