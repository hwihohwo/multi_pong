import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

class App {
	constructor() {
		const divContainer = document.querySelector("#webgl-container");
		this._divContainer = divContainer;

		this._player_num = 0;

		const renderer = new THREE.WebGLRenderer({antialias: true});
		renderer.setPixelRatio(window.devicePixelRatio);
		divContainer.appendChild(renderer.domElement);
		// renderer.domElement -> canvas타입의 dom객체
		this._renderer = renderer;

		const scene = new THREE.Scene();
		this._scene = scene;

		this._p1score = 0;
		this._p2score = 0;

		const div_p1score = document.getElementById("p1-score");
		const div_p2score = document.getElementById("p2-score");

		this._div_p1score = div_p1score;
		this._div_p2score = div_p2score;

		this._setupBackground();
		this._setupCamera();
		this._setupLight();
		this._setupModel();
		this._setupControls();
		this._setupKeyboardControls();
		this._setupSocket();

		window.onresize = this.resize.bind(this);
		//window.onresize -> 창크기 변경시 발생하는 메서드
		this.resize(); //renderer와 camera의 속성을 창크기에 맞게 설정해주기 위함.
		requestAnimationFrame(this.render.bind(this));
	}

	_setupControls() {
		new OrbitControls(this._camera, this._divContainer);
	}

	_setupBackground() {
		const loader = new THREE.TextureLoader();

		loader.load(
	    	WAVE_PATH,
	    	(texture) => {
	        	this._scene.background = texture;
	    	},
		);
	}

	_sleep(sec) {
		let start = Date.now(), now = start;
		while (now - start < sec * 1000) {
			now = Date.now();
		}
	}

	_setupSocket() {
		const url = 'ws://localhost:8000/pong/';
		const socket = new WebSocket(url);

		socket.onopen = function(event) {
			console.log('WebSocket이 열렸습니다.');
		}

		socket.onmessage = function(event) {
			const data = JSON.parse(event.data);
			switch (data.type) {
				case 'game_over_disconnected':
					if (data.detail === 'game_over') {
						console.log("player " + data.winner + " win!");
					} else if (data.detail === 'game_over_disconnected') {
						console.log("Opponent disconnected! " + "player " + data.winner + " win!");
					}
					this._socket.close();
					break;
				case 'player_num':
					this._player_num = data.player_num;
					this._camera.position.set((this._player_num === 1) ? -3.0 : 3.0, 2, 0);
					this._camera.lookAt(0, -1, 0);
					break;
				case 'positions':
					this._sphere.position.set(...data.sphere_position);
					this._cube_1.position.set(...data.p1_bar_position);
					this._cube_2.position.set(...data.p2_bar_position);
					break;
				case 'scores':
					this._p1score = data.player_1_score;
					this._p2score = data.player_2_score;
					break;
			}
		}.bind(this);
		
		socket.onclose = function(event) {
			console.log('WebSocket이 닫혔습니다.');
		}

		this._socket = socket;
	}

	_setupKeyboardControls() {
		const keyboardState = {};
		this._keyboardState = keyboardState;

		document.addEventListener('keydown', (event) => {
			keyboardState[event.code] = true;
		});
		document.addEventListener('keyup', (event) => {
			keyboardState[event.code] = false;
		});
	}

	_setupCamera() {
		const width = this._divContainer.clientWidth;
		const height = this._divContainer.clientHeight;
		// const camera = new THREE.OrthographicCamera(
		// 	-5,
		// 	5,
		// 	2,
		// 	-2,
		// 	0.1,
		// 	100
		// );
		const camera = new THREE.PerspectiveCamera(
			75,
			width / height,
			0.1,
			100
		);
		const cam_pos = new THREE.Vector3(0, 0, 3);
		camera.position.copy(cam_pos);
		camera.lookAt(0, 0, 0);
		this._camera = camera;
	}

	_setupLight() {
		const light = new THREE.AmbientLight(0xffffff, 0.2);

		this._scene.add(light);
		this._light = light;

		const color = 0xffffff; // 광원의 색상.
		const intensity = 1; //광원의 세기.
		const direct_light = new THREE.DirectionalLight(color, intensity);
		direct_light.position.set(-1, 2, 4);
		this._scene.add(direct_light);
		this._direct_light = direct_light;
	}

	_setupGround() {
		// const UpperPlane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), -3.0);
		// const LowerPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), -3.0);
		// const RightSidePlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), -2.5);
		// const LeftSidePlane = new THREE.Plane(new THREE.Vector3(0, 0, -1), -2.5);

		// this._UpperPlane = UpperPlane;
		// this._LowerPlane = LowerPlane;
		// this._RightSidePlane = RightSidePlane;
		// this._LeftSidePlane = LeftSidePlane;

		// const UpperPlaneHelper = new THREE.PlaneHelper( UpperPlane, 6, 0xff0000 );
		// this._scene.add( UpperPlaneHelper );
		// const LowerPlaneHelper = new THREE.PlaneHelper( LowerPlane, 6, 0xffff00 );
		// this._scene.add( LowerPlaneHelper );
		// const RightSidePlaneHelper = new THREE.PlaneHelper( RightSidePlane, 3, 0x0000ff );
		// this._scene.add( RightSidePlaneHelper );
		// const LeftSidePlaneHelper = new THREE.PlaneHelper( LeftSidePlane, 3, 0xffffff );
		// this._scene.add( LeftSidePlaneHelper );

		const loader = new THREE.TextureLoader();
		loader.load(GROUND_PATH, (texture) => {
			texture.encoding = THREE.sRGBEncoding;
			const material = new THREE.MeshBasicMaterial({
				map: texture,
				side: THREE.DoubleSide,
			});
			const geometry = new THREE.PlaneGeometry( 5, 6 );
			const BottomPlane = new THREE.Mesh( geometry, material );
			BottomPlane.rotation.x = Math.PI / 2;
			BottomPlane.position.y = -0.1;		
			this._scene.add(BottomPlane);
			this._BottomPlane = BottomPlane;
		});
	}

	_setupModel() {
		this._setupGround();

		// const Boxgeometry = new THREE.BoxGeometry(0.1, 0.08, 0.7); // 인자 : 가로, 세로, 깊이
		// const Boxmaterial_1 = new THREE.MeshStandardMaterial({
		// 	color: 0xff0000});
		// const Boxmaterial_2 = new THREE.MeshStandardMaterial({
		// 		color: 0x00ff00});

		// const cube_1 = new THREE.Mesh(Boxgeometry, Boxmaterial_1);
		// cube_1.position.x = 2.5;

		// const cube_2 = new THREE.Mesh(Boxgeometry, Boxmaterial_2);
		// cube_2.position.x = -2.5;

		// this._scene.add(cube_2);
		// this._scene.add(cube_1);
		// this._cube_1 = cube_1;
		// this._cube_2 = cube_2;

		let loader = new GLTFLoader();
		loader.load(MODEL_PATH, (gltf) => {
			const model_1 = gltf.scene;
			const model_2 = gltf.scene.clone();
			model_1.scale.set(0.1, 0.1, 0.1);
			model_1.position.x = -2.5;
			model_1.rotation.y = Math.PI / 2;
			model_2.scale.set(0.1, 0.1, 0.1);
			model_2.position.x = 2.5;
			model_2.rotation.y = -Math.PI / 2;
			// model_2.rotation.y = Math.PI;
			this._scene.add(model_1);
			this._scene.add(model_2);
			this._cube_1 = model_1;
			this._cube_2 = model_2;
		});

		loader = new THREE.TextureLoader();
		loader.load(BALL_PATH, (texture) => {
			// texture.encoding = THREE.sRGBEncoding;
			const Spherematerial = new THREE.MeshBasicMaterial({
				map: texture,
			});
			const Spheregeometry = new THREE.SphereGeometry(0.04, 32, 32);
			const sphere = new THREE.Mesh(Spheregeometry, Spherematerial);
			this._scene.add(sphere);
			this._sphere = sphere;
		});

		this._rotation_speed = 0.05;

		// const Spherematerial = new THREE.MeshStandardMaterial({
		// 	color: 0xffffff});
	}

	resize() { 
		const width = this._divContainer.clientWidth;
		const height = this._divContainer.clientHeight;

		this._camera.aspect = width / height;
		this._camera.updateProjectionMatrix();

		this._renderer.setSize(width, height);
	}

	render(time) {
   		this._renderer.render(this._scene, this._camera);
		this.update(time);
   		requestAnimationFrame(this.render.bind(this));
	}

	_CheckKeyboardInput() {
		const keyMapping = this._player_num === 1 ? 
			{ 'ArrowRight': 'ArrowRight', 'ArrowLeft': 'ArrowLeft' } : 
			{ 'ArrowRight': 'ArrowLeft', 'ArrowLeft': 'ArrowRight' };
	
		['ArrowRight', 'ArrowLeft'].forEach((key) => {
			if (this._socket.readyState === WebSocket.OPEN && this._keyboardState[key]) {
				this._socket.send(JSON.stringify({
					'type': 'keydown',
					'keycode': keyMapping[key],
					'player_num': this._player_num
				}));
			}
		});
	}
	
	update( time ) {
		this._CheckKeyboardInput();

		if (this._sphere) {
			this._sphere.rotation.x += this._rotation_speed;
			this._sphere.rotation.y += this._rotation_speed;
			this._sphere.rotation.z += this._rotation_speed;
		}

		this._div_p1score.innerHTML = "P1 Score : " + this._p1score;
		this._div_p2score.innerHTML = "P2 Score : " + this._p2score;
	}
}

window.onload = function() {
	new App();
}