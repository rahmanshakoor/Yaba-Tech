import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class ItemType(str, enum.Enum):
    RAW = "Raw"
    PREPPED = "Prepped"
    DISH = "Dish"


class WasteReason(str, enum.Enum):
    SPOILED = "Spoiled"
    DROPPED = "Dropped"
    BURNED = "Burned"
    THEFT = "Theft"


class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    unit = Column(String, nullable=False)  # kg, liter, etc.
    shelf_life_days = Column(Integer, nullable=False, default=0)
    type = Column(Enum(ItemType), nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Relationships
    compositions_as_output = relationship(
        "ItemComposition",
        foreign_keys="ItemComposition.output_item_id",
        back_populates="output_item",
        cascade="all, delete-orphan",
    )
    compositions_as_input = relationship(
        "ItemComposition",
        foreign_keys="ItemComposition.input_item_id",
        back_populates="input_item",
    )
    inventory_batches = relationship(
        "ItemsInventory", back_populates="item", cascade="all, delete-orphan"
    )


class ItemComposition(Base):
    __tablename__ = "item_compositions"

    composition_id = Column(Integer, primary_key=True, autoincrement=True)
    output_item_id = Column(
        Integer, ForeignKey("items.item_id"), nullable=False
    )
    input_item_id = Column(
        Integer, ForeignKey("items.item_id"), nullable=False
    )
    quantity_required = Column(Float, nullable=False)

    # Relationships
    output_item = relationship(
        "Item",
        foreign_keys=[output_item_id],
        back_populates="compositions_as_output",
    )
    input_item = relationship(
        "Item",
        foreign_keys=[input_item_id],
        back_populates="compositions_as_input",
    )


class ItemsInventory(Base):
    __tablename__ = "items_inventory"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    quantity_current = Column(Float, nullable=False)
    quantity_initial = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False, default=0.0)
    expiration_date = Column(DateTime, nullable=True)
    source_invoice_id = Column(
        Integer, ForeignKey("invoices.invoice_id"), nullable=True
    )
    source_production_id = Column(
        Integer, ForeignKey("production_logs.log_id"), nullable=True
    )
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    item = relationship("Item", back_populates="inventory_batches")
    source_invoice = relationship("Invoice", back_populates="inventory_batches")
    used_in_production = relationship(
        "ProductionLog",
        foreign_keys="ProductionLog.input_batch_id",
        back_populates="input_batch",
    )
    produced_from = relationship(
        "ProductionLog",
        foreign_keys="ProductionLog.output_batch_id",
        back_populates="output_batch",
    )


class ProductionLog(Base):
    __tablename__ = "production_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    output_batch_id = Column(
        Integer, ForeignKey("items_inventory.batch_id"), nullable=False
    )
    input_batch_id = Column(
        Integer, ForeignKey("items_inventory.batch_id"), nullable=False
    )
    quantity_used = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    output_batch = relationship(
        "ItemsInventory",
        foreign_keys=[output_batch_id],
        back_populates="produced_from",
    )
    input_batch = relationship(
        "ItemsInventory",
        foreign_keys=[input_batch_id],
        back_populates="used_in_production",
    )


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_name = Column(String, nullable=False)
    total_cost = Column(Float, nullable=False, default=0.0)
    invoice_date = Column(DateTime, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    inventory_batches = relationship(
        "ItemsInventory", back_populates="source_invoice"
    )


class WasteLog(Base):
    __tablename__ = "waste_logs"

    waste_id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(
        Integer, ForeignKey("items_inventory.batch_id"), nullable=False
    )
    quantity = Column(Float, nullable=False)
    reason = Column(Enum(WasteReason), nullable=False)
    cost_loss = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    batch = relationship("ItemsInventory")
