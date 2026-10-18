from erp_fastapi.models import InventoryItem, Order, User
from erp_fastapi.models.integration import IntegrationOperation
from erp_fastapi.auth import hash_password, verify_password


def order(status='draft', qty=3, kind='sale'):
    return dict(order_type=kind, partner_type='company', partner_id=1, date='2026-10-18', status=status,
                items=[dict(product_id=1, quantity=qty, unit_price=15, vat_percent=11, discount_percent=5)])

def stock(sessions):
    with sessions() as db:
        i=db.get(InventoryItem,1);return i.quantity,i.reserved


def test_reserve_complete_and_replay(env):
    c,s,h=env
    r=c.post('/orders/',json=order('confirmed'),headers=h(2));assert r.status_code==201,r.text
    oid=r.json()['id'];assert stock(s)==(10,3)
    assert c.put(f'/orders/{oid}',json={'status':'completed'},headers=h(2)).status_code==200
    assert stock(s)==(7,0)
    assert c.put(f'/orders/{oid}',json={'status':'completed'},headers=h(2)).status_code==200
    assert stock(s)==(7,0)
    assert c.delete(f'/orders/{oid}',headers=h()).status_code==409


def test_cancel_releases(env):
    c,s,h=env;oid=c.post('/orders/',json=order('confirmed'),headers=h()).json()['id']
    assert c.put(f'/orders/{oid}',json={'status':'cancelled'},headers=h()).status_code==200
    assert stock(s)==(10,0)


def test_insufficient_stock_rolls_back_order(env):
    c,s,h=env
    assert c.post('/orders/',json=order('confirmed',11),headers=h()).status_code==409
    assert stock(s)==(10,0)
    with s() as db: assert db.query(Order).count()==0


def test_aggregates_duplicate_lines(env):
    c,s,h=env;p=order('confirmed',6);p['items']*=2
    assert c.post('/orders/',json=p,headers=h()).status_code==409
    assert stock(s)==(10,0)


def test_purchase_and_return(env):
    c,s,h=env
    for kind,expected in [('purchase',(13,0)),('return_sale',(16,0)),('return_purchase',(13,0))]:
        assert c.post('/orders/',json=order('completed',3,kind),headers=h()).status_code==201
        assert stock(s)==expected


def test_draft_has_no_effect_and_invalid_partner(env):
    c,s,h=env
    assert c.post('/orders/',json=order(),headers=h()).status_code==201
    assert stock(s)==(10,0)
    p=order();p['partner_id']=999
    assert c.post('/orders/',json=p,headers=h()).status_code==400
    p=order();p['items'][0]['product_id']=999
    assert c.post('/orders/',json=p,headers=h()).status_code==400


def test_invalid_updates_and_manual_stock(env):
    c,s,h=env;oid=c.post('/orders/',json=order(),headers=h()).json()['id']
    for patch in ({'status':'invalid'},{'order_type':'nonsense'},{'partner_type':'bogus'},{'items':[]},{'status':None}):
        assert c.put(f'/orders/{oid}',json=patch,headers=h()).status_code==422
    assert c.put('/inventory/1',json={'quantity':-1},headers=h()).status_code==422
    assert c.put('/inventory/1',json={'reserved':2},headers=h()).status_code==400
    c.put(f'/orders/{oid}',json={'status':'confirmed'},headers=h())
    assert c.put('/inventory/1',json={'quantity':2},headers=h()).status_code==409
    assert stock(s)==(10,3)


def test_import_deduplicates_and_reserves_once(env):
    c,s,h=env;p=dict(channel='emag',external_id='123',order=order('confirmed'))
    first=c.post('/integrations/orders/import',json=p,headers=h());assert first.status_code==200,first.text
    second=c.post('/integrations/orders/import',json=p,headers=h())
    assert first.json()['created'] is True and second.json()['created'] is False
    assert first.json()['order_id']==second.json()['order_id'];assert stock(s)==(10,3)


def test_access_controls(env,monkeypatch):
    c,s,h=env;monkeypatch.delenv('ALLOW_REGISTRATION',raising=False)
    assert c.post('/auth/register',json={'name':'X','email':'x@test.ro','password':'123456'}).status_code==403
    assert c.get('/users/',headers=h(2)).status_code==403
    assert c.put('/users/1',json={'role_id':1},headers=h(2)).status_code==403
    assert c.post('/orders/',json=order(),headers=h(3)).status_code==403
    assert c.get('/orders/',headers=h(3)).status_code==200
    assert c.get('/roles/').status_code==401
    assert c.put('/auth/me',json={'name':'Operator','email':'operator@test.ro'},headers=h(2)).status_code==200
    with s.begin() as db:db.get(User,2).is_active=False
    assert c.get('/orders/',headers=h(2)).status_code==401
    assert c.post('/auth/login',json={'email':'operator@test.ro','password':'test-password'}).status_code==401


def test_admin_creates_user(env):
    c,s,h=env
    r=c.post('/users/',json={'name':'New','email':'new@test.ro','password':'long-password','role_id':2},headers=h())
    assert r.status_code==201,r.text


def test_password_legacy_upgrade(env):
    import hashlib
    c,s,h=env;salt='old-salt';old=salt+'$'+hashlib.sha256((salt+'test-password').encode()).hexdigest()
    assert verify_password('test-password',old)
    with s.begin() as db:db.get(User,2).hashed_password=old
    assert c.post('/auth/login',json={'email':'operator@test.ro','password':'test-password'}).status_code==200
    with s() as db:assert db.get(User,2).hashed_password.startswith('scrypt$')
    assert verify_password('test-password',hash_password('test-password'))
    assert not verify_password('wrong',hash_password('test-password'))


def test_invoice_once_and_uncertain_no_retry(env,monkeypatch):
    from fastapi import HTTPException
    from erp_fastapi.integrations import smartbill
    monkeypatch.setenv('SMARTBILL_COMPANY_VAT_CODE','ROTEST')
    c,s,h=env;oid=c.post('/orders/',json=order('confirmed'),headers=h()).json()['id'];calls=[]
    def send(p):calls.append(p);return {'series':'TEST','number':'1'}
    monkeypatch.setattr(smartbill,'create_invoice',send)
    for _ in range(2):
        r=c.post(f'/integrations/smartbill/orders/{oid}/invoice',json={'payload':{'seriesName':'TEST','client':{'name':'Customer','country':'Romania'}}},headers=h());assert r.status_code==200,r.text
    assert len(calls)==1
    assert calls[0]["products"][0]["price"]==14.25
    assert calls[0]["products"][0]["taxPercentage"]==11
    oid=c.post('/orders/',json=order('confirmed'),headers=h()).json()['id']
    def fail(p):calls.append(p);raise HTTPException(502,'timeout')
    monkeypatch.setattr(smartbill,'create_invoice',fail)
    assert c.post(f'/integrations/smartbill/orders/{oid}/invoice',json={'payload':{'seriesName':'TEST','client':{'name':'Customer','country':'Romania'}}},headers=h()).status_code==502
    assert c.post(f'/integrations/smartbill/orders/{oid}/invoice',json={'payload':{'seriesName':'TEST','client':{'name':'Customer','country':'Romania'}}},headers=h()).status_code==409
    assert len(calls)==2


def test_legacy_requires_adoption(env):
    c,s,h=env
    with s.begin() as db:
        o=Order(order_type='sale',partner_id=1,partner_type='company',date='2026-01-01',status='confirmed',workflow_managed=False)
        from erp_fastapi.models import OrderLine
        o.items=[OrderLine(product_id=1,quantity=2,unit_price=10)]
        db.add(o);db.flush();oid=o.id
    assert c.put(f'/orders/{oid}',json={'status':'completed'},headers=h()).status_code==409
    assert stock(s)==(10,0)
    assert c.post(f'/orders/{oid}/adopt-stock',headers=h()).status_code==200
    assert stock(s)==(10,2)
    assert c.post(f'/orders/{oid}/adopt-stock',headers=h()).status_code==200
    assert stock(s)==(10,2)
    assert c.put(f'/orders/{oid}',json={'status':'completed'},headers=h()).status_code==200
    assert stock(s)==(8,0)


def test_order_optimistic_concurrency(env):
    from sqlalchemy.orm.exc import StaleDataError
    import pytest
    c,s,h=env;oid=c.post('/orders/',json=order(),headers=h()).json()['id']
    with s() as first, s() as second:
        a=first.get(Order,oid);b=second.get(Order,oid)
        a.status='confirmed';first.commit()
        b.status='completed'
        with pytest.raises(StaleDataError):second.flush()


def test_self_lockout_prevented(env):
    c,s,h=env
    assert c.delete('/users/1',headers=h()).status_code==409
    assert c.put('/users/1',json={'is_active':False},headers=h()).status_code==409
    assert c.put('/roles/1',json={'name':'other'},headers=h()).status_code==409


def test_provider_clients(env,monkeypatch):
    import httpx
    from erp_fastapi.integrations import emag, smartbill, shopify, common
    monkeypatch.setenv('INTEGRATIONS_ENABLED','true')
    for key in ('EMAG_USERNAME','EMAG_PASSWORD','SMARTBILL_EMAIL','SMARTBILL_TOKEN'):
        monkeypatch.setenv(key,'test-only')
    monkeypatch.setenv('SMARTBILL_COMPANY_VAT_CODE','ROTEST')
    monkeypatch.setenv('SHOPIFY_SHOP','test-shop.myshopify.com')
    monkeypatch.setenv('SHOPIFY_ACCESS_TOKEN','test-only')
    calls=[]
    def request(method,url,**kw):
        calls.append((method,url,kw))
        if 'emag' in url:
            return httpx.Response(200,json={'isError':False,'results':[{'id':123}]})
        if 'smartbill' in url:
            return httpx.Response(200,json={'errorText':'','series':'TEST','number':'001'})
        return httpx.Response(200,json={'data':{'inventorySetQuantities':{'userErrors':[]}}})
    monkeypatch.setattr(emag,'request',request);monkeypatch.setattr(smartbill,'request',request);monkeypatch.setattr(shopify,'request',request)
    assert emag.fetch_emag_orders({'id':123})==[{'id':123}]
    assert calls[-1][2]['json']=={'id':123}
    emag.update_stock_in_emag(99,7)
    assert calls[-1][2]['json']['data'][0]['stock'][0]['value']==7
    assert smartbill.create_invoice({'companyVatCode':'ROTEST'})['number']=='001'
    shopify.update_stock('gid://shopify/InventoryItem/1','gid://shopify/Location/1',7,10,'unique-key-123456')
    variables=calls[-1][2]['json']['variables']
    assert variables['input']['quantities'][0]['compareQuantity']==10
    assert '@idempotent' in calls[-1][2]['json']['query']


def test_disabled_integrations_do_not_leave_pending(env,monkeypatch):
    c,s,h=env;monkeypatch.setenv('INTEGRATIONS_ENABLED','false');monkeypatch.setenv('SMARTBILL_COMPANY_VAT_CODE','ROTEST')
    oid=c.post('/orders/',json=order('confirmed'),headers=h()).json()['id']
    for _ in range(2):
        assert c.post(f'/integrations/smartbill/orders/{oid}/invoice',json={'payload':{'seriesName':'TEST','client':{'name':'Customer'}}},headers=h()).status_code==503
    with s() as db:assert db.query(IntegrationOperation).count()==0
