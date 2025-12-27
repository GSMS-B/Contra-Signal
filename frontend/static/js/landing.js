document.addEventListener('DOMContentLoaded', () => {
    // --- 1. ANIMATION SETUP (GSAP) ---
    // Custom "SplitText" implementation for letters/lines since we don't have the plugin
    const h1 = document.getElementById('hero-title');
    const p = document.getElementById('hero-desc');
    const ctas = document.getElementById('hero-ctas');
    const bgContainer = document.getElementById('canvas-container');

    // Helper to wrap lines/words (Simple version: just treat whole block for now to ensure smoothness, 
    // or split by words if user wants granulatiry. Let's do simple fade up for stability).

    // Initial States
    gsap.set(bgContainer, { filter: "blur(28px)" });
    gsap.set([h1, p, ctas], { opacity: 0, y: 24, filter: "blur(8px)" });

    // Timeline
    const tl = gsap.timeline({ defaults: { ease: "power2.out" } });

    tl.to(bgContainer, { filter: "blur(0px)", duration: 1.5 }, 0)
        .to(h1, { opacity: 1, y: 0, filter: "blur(0px)", duration: 1 }, 0.3)
        .to(p, { opacity: 1, y: 0, filter: "blur(0px)", duration: 1 }, 0.5)
        .to(ctas, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.8 }, 0.7);


    // --- 2. THREE.JS SHADER SETUP ---
    const container = document.getElementById('canvas-container');

    // Scence Setup
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
    camera.position.z = 1;

    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Shader Code (Ported from React component)
    const vertexShader = `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = vec4(position, 1.0);
        }
    `;

    const fragmentShader = `
        precision highp float;

        varying vec2 vUv;
        uniform float u_time;
        uniform vec3 u_resolution;
        
        #define STEP 256
        #define EPS .001

        float smin( float a, float b, float k ) {
            float h = clamp( 0.5+0.5*(b-a)/k, 0.0, 1.0 );
            return mix( b, a, h ) - k*h*(1.0-h);
        }

        const mat2 m = mat2(.8,.6,-.6,.8);

        float noise( in vec2 x ) {
            return sin(1.5*x.x)*sin(1.5*x.y);
        }

        float fbm6( vec2 p ) {
            float f = 0.0;
            f += 0.500000*(0.5+0.5*noise( p )); p = m*p*2.02;
            f += 0.250000*(0.5+0.5*noise( p )); p = m*p*2.03;
            f += 0.125000*(0.5+0.5*noise( p )); p = m*p*2.01;
            f += 0.062500*(0.5+0.5*noise( p )); p = m*p*2.04;
            f += 0.015625*(0.5+0.5*noise( p ));
            return f/0.96875;
        }

        mat2 getRot(float a) {
            float sa = sin(a), ca = cos(a);
            return mat2(ca,-sa,sa,ca);
        }

        vec3 _position;

        float sphere(vec3 center, float radius) {
            return distance(_position,center) - radius;
        }

        float swingPlane(float height) {
            vec3 pos = _position + vec3(0.,0.,u_time * 5.5);
            float def =  fbm6(pos.xz * .25) * 0.5;
            
            float way = pow(abs(pos.x) * 34. ,2.5) *.0000125;
            def *= way;
            
            float ch = height + def;
            return max(pos.y - ch,0.);
        }

        float map(vec3 pos) {
            _position = pos;
            
            float dist;
            dist = swingPlane(0.);
            
            float sminFactor = 5.25;
            dist = smin(dist,sphere(vec3(0.,-15.,80.),60.),sminFactor);
            return dist;
        }

        void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
            vec2 uv = (fragCoord.xy-.5*u_resolution.xy)/u_resolution.y;
            
            vec3 rayOrigin = vec3(uv + vec2(0.,6.), -1. );
            vec3 rayDir = normalize(vec3(uv , 1.));
            
            rayDir.zy = getRot(.15) * rayDir.zy;
            
            vec3 position = rayOrigin;
            
            float curDist;
            int nbStep = 0;
            
            for(int i = 0; i < STEP; i++) {
                // Approximate texture fetch simply as noise or remove if unneeded 
                // The original code had texture(iChannel0...) which we don't have.
                // We'll skip the texture displacement for simplicity in vanilla port 
                // or replicate with simple noise if needed.
                // Simplified raymarching step:
                curDist = map(position);
                
                if(curDist < EPS) break;
                position += rayDir * curDist * .5;
                nbStep++;
            }
            
            float f;
            float dist = distance(rayOrigin,position);
            f = dist /(98.);
            f = float(nbStep) / float(STEP);
            
            f *= .9;
            vec3 col = vec3(f);
            
            fragColor = vec4(col,1.0);
        }

        void main() {
            mainImage(gl_FragColor, vUv * u_resolution.xy);
        }
    `;

    // Uniforms
    const uniforms = {
        u_time: { value: 0 },
        u_resolution: { value: new THREE.Vector3(window.innerWidth, window.innerHeight, 1) }
    };

    // Mesh
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
        vertexShader,
        fragmentShader,
        uniforms
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Resize Handler
    window.addEventListener('resize', () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        uniforms.u_resolution.value.set(window.innerWidth, window.innerHeight, 1);
    });

    // Animation Loop
    const clock = new THREE.Clock(); // Use THREE clock for u_time

    function animate() {
        requestAnimationFrame(animate);
        uniforms.u_time.value = clock.getElapsedTime() * 0.5; // Match React's * 0.5
        renderer.render(scene, camera);
    }

    animate();
});
