def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "member@test.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "member@test.com"
    assert data["user"]["role"] == "MEMBER"

def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "member@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_mock_login_role_switching(client):
    # Member mock login
    resp_member = client.post("/api/auth/mock-login", json={"role": "MEMBER"})
    assert resp_member.status_code == 200
    assert resp_member.json()["user"]["role"] == "MEMBER"

    # Agent mock login
    resp_agent = client.post("/api/auth/mock-login", json={"role": "AGENT"})
    assert resp_agent.status_code == 200
    assert resp_agent.json()["user"]["role"] == "AGENT"

    # Support Head mock login
    resp_head = client.post("/api/auth/mock-login", json={"role": "SUPPORT_HEAD"})
    assert resp_head.status_code == 200
    assert resp_head.json()["user"]["role"] == "SUPPORT_HEAD"

def test_me_authenticated(client, member_headers):
    response = client.get("/api/auth/me", headers=member_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "member@test.com"
    assert data["role"] == "MEMBER"

def test_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_role_based_access_control(client, member_headers, agent_headers, admin_headers):
    # Member cannot access admin metrics
    resp_member_admin = client.get("/api/admin/metrics", headers=member_headers)
    assert resp_member_admin.status_code == 403

    # Agent cannot access admin metrics
    resp_agent_admin = client.get("/api/admin/metrics", headers=agent_headers)
    assert resp_agent_admin.status_code == 403

    # Support Head can access admin metrics
    resp_head_admin = client.get("/api/admin/metrics", headers=admin_headers)
    assert resp_head_admin.status_code == 200
